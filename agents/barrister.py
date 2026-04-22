# agents/barrister.py — Barrister Agent (Local Ollama)

from typing import Optional, Dict, Any, List
import logging
import json
import os

from .auditor import StructuredDenial
from .clinician import EvidenceList

logger = logging.getLogger("BarristerAgent")
logger.setLevel(logging.INFO)

DEBUG_OUTPUT_DIR = "data/output"


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
            title = (
                getattr(it, "article_title", None)
                or it.get("article_title", "Untitled Article")
            )
            summary = (
                getattr(it, "summary_of_finding", None)
                or it.get("summary_of_finding", "No summary provided.")
            )
            pmid = (
                getattr(it, "pubmed_id", None)
                or it.get("pubmed_id", "N/A")
            )
            lines.append(f"- {title}: {summary} (PubMed: {pmid})")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Failed to format clinical evidence: {e}")
        return "- Clinical evidence formatting error."


# ============================================================
# BARRISTER AGENT
# ============================================================
def run_barrister_agent(
    client,
    denial_details: StructuredDenial = None,
    clinical_evidence: EvidenceList = None,
    regulatory_evidence: Dict[str, Any] = None,
    critique: str = None,
    emit: Any = None,
    **kwargs
) -> Optional[str]:

    denial = denial_details
    clinical = clinical_evidence
    regulatory = regulatory_evidence

    logger.info("[Barrister] Preparing appeal generation...")

    # ── Format supporting evidence ────────────────────────────────────────
    clinical_text = format_clinical_evidence(clinical)
    legal_points = extract_legal_points(regulatory)

    if legal_points:
        legal_text = "\n".join(
            f"- {lp.get('statute', 'Statute')}: "
            f"{lp.get('summary', lp.get('argument', 'No summary'))}"
            for lp in legal_points
        )
    else:
        legal_text = "- No statutory or regulatory arguments produced."

    # ── System instruction ────────────────────────────────────────────────
    system_instruction = (
        "You are the Barrister Agent — a senior appellate attorney specializing "
        "in health insurance disputes.\n"
        "Your job is to produce a polished, persuasive, fully structured appeal letter.\n"
        "Write in formal legal prose. No placeholders. No incomplete sections.\n"
        "Use the clinical and regulatory evidence provided.\n"
        "Do not add any commentary before or after the letter.\n"
        "Output the letter text only."
    )

    if critique:
        system_instruction += f"\n\nIMPORTANT DEBATE FEEDBACK: The Judge agent rejected your previous draft. The Judge provided this critique: '{critique}'. You MUST revise your letter to address these issues."

    # ── Prompt ───────────────────────────────────────────────────────────
    # Note: removed markdown ** bold markers — Mistral sometimes echoes
    # them literally into the output which looks bad in the PDF.
    prompt = f"""Draft a complete formal insurance appeal letter using the information below.

DENIAL DETAILS
--------------
Procedure: {denial.procedure_denied}
Denial Code: {denial.denial_code}
Insurer Reason: {denial.insurer_reason_snippet}
Policy Clause: {denial.policy_clause_text}

CLINICAL EVIDENCE
-----------------
{clinical_text}

REGULATORY FINDINGS
-------------------
{legal_text}

REQUIRED STRUCTURE
------------------
1. Subject line referencing the procedure and denial code.
2. Opening paragraph: summarize the denial and state intent to appeal.
3. Section I - Clinical Argument: use the clinical evidence above.
4. Section II - Legal Argument: reference the regulatory findings above.
5. Conclusion: firm request for reversal and clear next steps.

Write the full letter now:"""

    logger.info("[Barrister] Sending prompt to Ollama...")

    def stream_callback(chunk: str):
        if emit:
            emit({"type": "agent_stream", "agent": "barrister", "chunk": chunk})

    appeal_text = client.generate(
        prompt=prompt,
        system=system_instruction,
        temperature=0.3,
        max_tokens=2048,
        json_mode=False,    # plain text output, not JSON
        stream_callback=stream_callback,
    )

    if not appeal_text or len(appeal_text.strip()) < 100:
        logger.error("[Barrister] Empty or too-short response from Ollama.")
        _save_debug(appeal_text or "", "barrister_raw.txt")
        return None

    appeal_text = appeal_text.strip()

    # ── Save debug copy ───────────────────────────────────────────────────
    _save_debug(appeal_text, "barrister_raw.txt")

    logger.info(f"[Barrister] Appeal letter generated ({len(appeal_text)} chars).")
    return appeal_text


# ============================================================
# Debug helper
# ============================================================
def _save_debug(content: str, filename: str):
    """Save raw output for inspection without crashing the pipeline."""
    try:
        os.makedirs(DEBUG_OUTPUT_DIR, exist_ok=True)
        with open(os.path.join(DEBUG_OUTPUT_DIR, filename), "w", encoding="utf-8") as fh:
            fh.write(content)
    except Exception as e:
        logger.warning(f"[Barrister] Could not save debug file: {e}")