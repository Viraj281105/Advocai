# agents/barrister.py
from google import genai
from google.genai import types
from typing import Optional, Dict, Any, List, Iterable
import json
import logging
from .auditor import StructuredDenial
from .clinician import EvidenceList

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------
BARRISTER_MODEL = "gemini-2.5-flash"
DEBUG_OUTPUT_DIR = "data/output"  # ensure this directory exists in your pipeline


# -------------------------------------------------------------
# Helper: Safely extract legal points
# -------------------------------------------------------------
def extract_legal_points(regulatory: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Safely extracts and validates the list of legal points from the Regulatory Agent output.
    Accepts dict, JSON string, or None. Returns list of dicts with at least 'argument' or 'statute'.
    """
    if not regulatory:
        return []

    # If a JSON string was provided, try to parse
    if isinstance(regulatory, str):
        try:
            regulatory = json.loads(regulatory)
        except json.JSONDecodeError:
            logger.error("Regulatory evidence is a non-JSON string. Cannot extract legal points.")
            return []
        except Exception as e:
            logger.error("Failed to parse regulatory JSON string: %s", e)
            return []

    # If the regulatory agent returned an error sentinel, skip
    if isinstance(regulatory, dict) and regulatory.get("violation") == "SYSTEM_ERROR":
        logger.warning("Regulatory Agent reported a SYSTEM_ERROR. Skipping legal points.")
        return []

    lp = regulatory.get("legal_points") if isinstance(regulatory, dict) else None

    if isinstance(lp, list):
        valid_points = []
        for point in lp:
            if isinstance(point, dict) and (point.get("statute") or point.get("argument") or point.get("summary")):
                valid_points.append(point)
            else:
                logger.warning("Skipping malformed legal point: %s", repr(point))
        return valid_points

    # Sometimes regulatory may include a single dict under 'legal_points' or other shape
    if isinstance(lp, dict):
        # wrap single dict
        return [lp] if (lp.get("statute") or lp.get("argument") or lp.get("summary")) else []

    logger.warning("Regulatory output does not contain a 'legal_points' list: %s", type(lp))
    return []


# -------------------------------------------------------------
# Helpers: clinical evidence formatting
# -------------------------------------------------------------
def _iter_evidence_items(clinical_evidence: EvidenceList) -> Iterable:
    """
    Yields evidence items from different possible clinical_evidence shapes:
    - Pydantic model with .root (list-like)
    - plain list of objects
    - None
    """
    if not clinical_evidence:
        return []
    # If it's a Pydantic model with attribute 'root' (your EvidenceList)
    if hasattr(clinical_evidence, "root") and isinstance(clinical_evidence.root, list):
        return clinical_evidence.root
    # If it's just a list already
    if isinstance(clinical_evidence, list):
        return clinical_evidence
    # Try to treat it as an iterable
    try:
        return list(clinical_evidence)
    except Exception:
        return []


def _format_clinical_evidence(clinical_evidence: EvidenceList) -> str:
    try:
        items = list(_iter_evidence_items(clinical_evidence))
        if not items:
            return "- **CRITICAL WARNING:** No clinical evidence was found or structured. The appeal will be weak."

        lines = []
        for e in items:
            # best-effort accessors to accommodate slightly different item shapes
            title = getattr(e, "article_title", None) or e.get("article_title") if isinstance(e, dict) else None
            summary = getattr(e, "summary_of_finding", None) or e.get("summary_of_finding") if isinstance(e, dict) else None
            pubmed = getattr(e, "pubmed_id", None) or e.get("pubmed_id") if isinstance(e, dict) else None

            title = (title or "Untitled Article").strip()
            summary = (summary or "No summary provided.").strip()
            pubmed = str(pubmed) if pubmed is not None else "NoRef"

            lines.append(f"- **{title}:** {summary} (Ref: {pubmed})")
        return "\n".join(lines)
    except Exception as exc:
        logger.exception("Failed to format clinical evidence: %s", exc)
        return "- **ERROR:** Clinical evidence formatting failed."


# -------------------------------------------------------------
# MAIN BARRISTER AGENT
# -------------------------------------------------------------
def run_barrister_agent(
    client: genai.Client,
    denial_details: StructuredDenial,
    clinical_evidence: EvidenceList,
    regulatory_evidence: Dict[str, Any]
) -> Optional[str]:

    logger.info("Assembling barrister prompt and evidence...")

    # clinical evidence formatting
    evidence_text = _format_clinical_evidence(clinical_evidence)

    # regulatory formatting
    legal_points = extract_legal_points(regulatory_evidence)
    if legal_points:
        regulatory_text = "\n".join([
            f"- **{lp.get('statute', 'Legal Point')}:** {lp.get('summary', lp.get('argument', 'No summary provided.'))}"
            for lp in legal_points
        ])
    else:
        regulatory_text = "- No regulatory or statutory findings were produced. Argument will rely heavily on clinical evidence and policy ambiguity."

    # System instruction
    system_instruction = (
        "You are the Barrister Agent, an expert appellate attorney specializing in "
        "health insurance disputes. Your objective is to draft a formal, highly persuasive "
        "appeal letter that leverages clinical evidence and regulatory statutes.\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. Directly rebut: Quote and directly counter the insurer's denial reason and policy clause, "
        "arguing that the evidence proves the procedure is no longer 'experimental'.\n"
        "2. Formatting: Use clear headings (e.g., I. Clinical Argument, II. Legal/Policy Argument).\n"
        "3. Placeholders: DO NOT leave placeholders like [Patient Name]. Use a neutral addressing such as 'To the Claims Review Department'.\n"
    )

    # Final prompt (concise, but includes required fields)
    final_prompt = f"""
Draft a formal, professional appeal letter based on the following structured data.

==========================================
1. INSURER DENIAL DETAILS (REQUIRED FOR REBUTTAL)
==========================================
Procedure Denied: {denial_details.procedure_denied}
Denial Code: {denial_details.denial_code}
Insurer's Reason: "{denial_details.insurer_reason_snippet}"
Policy Clause Cited: "{denial_details.policy_clause_text}"

==========================================
2. CLINICAL EVIDENCE (REQUIRED FOR SECTION I: CLINICAL ARGUMENT)
==========================================
Use these findings to argue that the procedure is safe, effective, and no longer experimental or unproven.
{evidence_text}

==========================================
3. REGULATORY & LEGAL FINDINGS (REQUIRED FOR SECTION II: LEGAL ARGUMENT)
==========================================
Use these points to argue the insurer's denial may violate statutory or regulatory requirements, or is based on an ambiguous exclusion.
{regulatory_text}

==========================================
LETTER STRUCTURE & TONE REQUIREMENTS
==========================================
1. Title: Use a formal Subject Line that includes the Denial Code and Procedure Name.
2. Opening: State the purpose of the letter (formal appeal) and quote the insurer's reason.
3. Section I - Clinical Argument: Cite article titles/refs and explain why the procedure meets medical necessity or accepted standards.
4. Section II - Legal/Policy Argument: Explain any statutory/regulatory issues or policy-interpretation problems supporting reversal.
5. Conclusion: End with a firm, unambiguous request for immediate reversal of the denial and next steps for administration.
"""

    logger.info("Sending prompt to model: %s", BARRISTER_MODEL)
    try:
        response = client.models.generate_content(
            model=BARRISTER_MODEL,
            contents=[final_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=2048,
                temperature=0.3,
            ),
        )

        # Defensive extraction of text (mirror approach from auditor)
        raw_text = None
        if hasattr(response, "text") and response.text:
            raw_text = response.text.strip()
        elif hasattr(response, "candidates") and response.candidates:
            try:
                candidate = response.candidates[0]
                if hasattr(candidate, "content") and candidate.content:
                    parts = [getattr(c, "text", str(c)) for c in candidate.content]
                    raw_text = "\n".join(parts).strip()
                else:
                    raw_text = getattr(candidate, "text", None)
            except Exception as _:
                raw_text = None

        if not raw_text:
            logger.error("Barrister model returned no text output. Saving raw candidate for debugging.")
            # best-effort dump
            try:
                with open(f"{DEBUG_OUTPUT_DIR}/barrister_raw_response.txt", "w", encoding="utf-8") as fh:
                    fh.write(repr(response))
            except Exception:
                pass
            return None

        # Save raw output for debugging traceability
        try:
            with open(f"{DEBUG_OUTPUT_DIR}/barrister_raw_response.txt", "w", encoding="utf-8") as fh:
                fh.write(raw_text)
        except Exception:
            pass

        logger.info("Barrister: generated appeal text (length=%d)", len(raw_text))
        return raw_text

    except Exception as exc:
        logger.exception("Failed to generate barrister letter: %s", exc)
        # Save exception details to debug file
        try:
            with open(f"{DEBUG_OUTPUT_DIR}/barrister_error.txt", "w", encoding="utf-8") as fh:
                fh.write(str(exc))
        except Exception:
            pass
        return None
