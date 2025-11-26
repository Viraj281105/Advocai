# agents/barrister.py — Enterprise-Stable Final Version

from google import genai
from google.genai import types
from typing import Optional, Dict, Any, List
import logging
import json
import os

from .auditor import StructuredDenial
from .clinician import EvidenceList

logger = logging.getLogger("BarristerAgent")
logger.setLevel(logging.INFO)

BARRISTER_MODEL = "gemini-2.5-flash"
DEBUG_OUTPUT_DIR = "data/output"


# ============================================================
# Unified Gemini Text Extractor
# ============================================================
def extract_text_from_gemini(resp) -> Optional[str]:
    """
    Extracts text from all possible Gemini response shapes.
    """
    if hasattr(resp, "text") and resp.text:
        return resp.text.strip()

    try:
        parts = resp.candidates[0].content.parts
        texts = [p.text for p in parts if getattr(p, "text", None)]
        return "\n".join(texts).strip() or None
    except Exception:
        return None


# ============================================================
# Safe legal points extractor
# ============================================================
def extract_legal_points(reg: Any) -> List[Dict[str, Any]]:
    """Safe extractor for regulatory legal_points list."""
    if not reg:
        return []

    if isinstance(reg, str):
        try:
            reg = json.loads(reg)
        except Exception:
            logger.error("Regulatory output string is invalid JSON.")
            return []

    if reg.get("violation") == "SYSTEM_ERROR":
        logger.warning("Regulatory agent returned SYSTEM_ERROR.")
        return []

    pts = reg.get("legal_points", [])
    if isinstance(pts, list):
        return [p for p in pts if isinstance(p, dict)]

    if isinstance(pts, dict):
        return [pts]

    return []


# ============================================================
# Clinical evidence formatter
# ============================================================
def format_clinical_evidence(ev: Any) -> str:
    """Handles EvidenceList, list, or empty structures gracefully."""
    try:
        if hasattr(ev, "root"):
            items = ev.root
        elif isinstance(ev, list):
            items = ev
        else:
            return "- No clinical evidence provided."

        if not items:
            return "- No clinical evidence provided."

        lines = []
        for it in items:
            title = getattr(it, "article_title", None) or it.get("article_title", "Untitled Article")
            summary = getattr(it, "summary_of_finding", None) or it.get("summary_of_finding", "No summary provided.")
            pmid = getattr(it, "pubmed_id", None) or it.get("pubmed_id", "N/A")

            lines.append(f"- **{title}:** {summary} (PubMed: {pmid})")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Failed to format clinical evidence: {e}")
        return "- Clinical evidence formatting error."


# ============================================================
# FINAL — Barrister Agent (orchestrator-compatible)
# ============================================================
def run_barrister_agent(
    client: genai.Client,
    denial_details: StructuredDenial = None,
    clinical_evidence: EvidenceList = None,
    regulatory_evidence: Dict[str, Any] = None,
    **kwargs
) -> Optional[str]:
    """
    FINAL orchestrator-compatible signature.
    Accepts keyword arguments:
    - denial_details
    - clinical_evidence
    - regulatory_evidence
    - **kwargs for future compatibility
    """

    # Rename for internal clarity
    denial = denial_details
    clinical = clinical_evidence
    regulatory = regulatory_evidence

    logger.info("[Barrister] Preparing appeal generation...")

    # -------------------------------------------------
    # Supporting Texts
    # -------------------------------------------------
    clinical_text = format_clinical_evidence(clinical)
    legal_points = extract_legal_points(regulatory)

    if legal_points:
        legal_text = "\n".join(
            f"- **{lp.get('statute', 'Statute')}** — {lp.get('summary', lp.get('argument', 'No summary'))}"
            for lp in legal_points
        )
    else:
        legal_text = "- No statutory or regulatory arguments produced."

    # -------------------------------------------------
    # System Instruction
    # -------------------------------------------------
    system_instruction = (
        "You are the Barrister Agent — a senior appellate attorney specializing in "
        "health insurance disputes. Your job is to produce a polished, persuasive, "
        "fully structured APPEAL LETTER.\n\n"
        "No placeholders. No incomplete sections. Use strong legal and medical reasoning."
    )

    # -------------------------------------------------
    # Prompt Assembly
    # -------------------------------------------------
    prompt = f"""
Draft a complete, formal appeal letter.

==============================================================
1. INSURER DENIAL DETAILS
==============================================================
Procedure: {denial.procedure_denied}
Denial Code: {denial.denial_code}
Insurer’s Reason: "{denial.insurer_reason_snippet}"
Policy Clause: "{denial.policy_clause_text}"

==============================================================
2. CLINICAL EVIDENCE (SECTION I)
==============================================================
{clinical_text}

==============================================================
3. REGULATORY FINDINGS (SECTION II)
==============================================================
{legal_text}

==============================================================
REQUIRED LETTER STRUCTURE
==============================================================
- Subject line referencing Procedure + Denial Code.
- Opening paragraph summarizing the denial and intent to appeal.
- Section I: Clinical argument using provided medical evidence.
- Section II: Legal/policy argument referencing statutory principles.
- Conclusion: Firm request for reversal + next steps.
"""

    # -------------------------------------------------
    # Model Invocation
    # -------------------------------------------------
    try:
        resp = client.models.generate_content(
            model=BARRISTER_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=2048,
                temperature=0.35,
            ),
        )
    except Exception as e:
        logger.exception("Barrister model API error: %s", e)
        return None

    # -------------------------------------------------
    # Extract Model Output
    # -------------------------------------------------
    appeal_text = extract_text_from_gemini(resp)

    if not appeal_text:
        logger.error("[Barrister] Empty response from model.")

        try:
            os.makedirs(DEBUG_OUTPUT_DIR, exist_ok=True)
            with open(f"{DEBUG_OUTPUT_DIR}/barrister_raw.txt", "w", encoding="utf-8") as fh:
                fh.write(repr(resp))
        except Exception:
            pass

        return None

    # Save raw
    try:
        os.makedirs(DEBUG_OUTPUT_DIR, exist_ok=True)
        with open(f"{DEBUG_OUTPUT_DIR}/barrister_raw.txt", "w", encoding="utf-8") as fh:
            fh.write(appeal_text)
    except:
        pass

    logger.info(f"[Barrister] Appeal letter generated ({len(appeal_text)} chars).")
    return appeal_text
