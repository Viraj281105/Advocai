# agents/clinician.py — Clinician Agent (Local Ollama)

from pydantic import BaseModel, Field
from typing import List, Optional
import json
import re
import logging

from .auditor import StructuredDenial
from tools.pubmed_search import pubmed_search

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ============================================================
# Pydantic Models
# ============================================================
class ClinicalEvidence(BaseModel):
    article_title: str
    summary_of_finding: str
    pubmed_id: str


class EvidenceList(BaseModel):
    root: List[ClinicalEvidence] = Field(default_factory=list)


# ============================================================
# Helper Functions
# ============================================================
def _clean_json(text: str) -> str:
    """Remove backticks, markdown fences, etc."""
    if not text:
        return ""
    t = text.strip()
    t = re.sub(r"```(?:json)?", "", t).replace("```", "")
    return t.strip()


def _derive_query(denial: StructuredDenial) -> str:
    """
    Generate an optimized PubMed query from denial details.
    Previously this was done by Gemini via function calling.
    Now done locally — fast, deterministic, no LLM needed.
    """
    reason = denial.insurer_reason_snippet.lower()
    procedure = denial.procedure_denied.strip()
    tags = []

    if "asymptomatic" in reason:
        tags.append("asymptomatic")

    if "experimental" in reason or "unproven" in reason:
        tags.append("clinical utility")

    if "not medically necessary" in reason or "medical necessity" in reason:
        tags.append("medical necessity")

    if "investigational" in reason:
        tags.append("randomized controlled trial")

    base = f"{procedure} clinical efficacy"
    return (base + " " + " ".join(tags)).strip() if tags else base


def _extract_first_json(text: str) -> Optional[dict]:
    """Balanced brace extraction for JSON recovery."""
    if not text:
        return None
    start = text.find("{")
    if start == -1:
        # maybe it's an array
        start = text.find("[")
        if start == -1:
            return None

    open_char = text[start]
    close_char = "}" if open_char == "{" else "]"
    depth = 0

    for i in range(start, len(text)):
        if text[i] == open_char:
            depth += 1
        elif text[i] == close_char:
            depth -= 1
            if depth == 0:
                block = text[start:i + 1]
                try:
                    return json.loads(block)
                except Exception:
                    cleaned = re.sub(r",\s*([}\]])", r"\1", block)
                    try:
                        return json.loads(cleaned)
                    except Exception:
                        return None
    return None


# ============================================================
# MAIN AGENT
# ============================================================
def run_clinician_agent(client, denial_details: StructuredDenial) -> EvidenceList:
    """
    SAFETY GUARANTEE:
      → ALWAYS returns EvidenceList (never None).
      → Even if PubMed fails or LLM fails.

    Flow:
      1. Derive optimized PubMed query locally (no LLM needed)
      2. Execute PubMed search
      3. Synthesize results into EvidenceList JSON via Ollama
    """

    # --------------------------------------------------------
    # STEP 1: Derive PubMed query locally
    # No LLM call needed here — pure deterministic logic
    # --------------------------------------------------------
    final_query = _derive_query(denial_details)
    logger.info(f"[Clinician] PubMed query: {final_query}")

    # --------------------------------------------------------
    # STEP 2: Execute PubMed search
    # --------------------------------------------------------
    logger.info(f"[Clinician] Executing pubmed_search()...")

    try:
        articles = pubmed_search(final_query)
        if not isinstance(articles, list):
            logger.warning("[Clinician] PubMed returned invalid type → empty list.")
            articles = []
    except Exception as e:
        logger.error(f"[Clinician] PubMed tool crashed: {e}")
        return EvidenceList(root=[])

    if not articles:
        logger.warning("[Clinician] PubMed returned zero articles.")
        return EvidenceList(root=[])

    logger.info(f"[Clinician] PubMed returned {len(articles)} articles.")

    # --------------------------------------------------------
    # STEP 3: Synthesize into EvidenceList JSON via Ollama
    # --------------------------------------------------------
    schema = EvidenceList.model_json_schema()

    sys_instr = (
        "You are the Clinician Agent.\n"
        "You will receive PubMed article data and must synthesize it into "
        "structured JSON matching the schema below.\n"
        "Output STRICT JSON ONLY. No markdown. No explanation.\n\n"
        f"Schema:\n{json.dumps(schema, indent=2)}\n\n"
        "Rules:\n"
        "- 'root' must be a list of article objects.\n"
        "- Each object needs: article_title, summary_of_finding, pubmed_id.\n"
        "- summary_of_finding: 1-2 sentence clinical finding summary.\n"
        "- If no articles provided, return: {\"root\": []}\n"
        "- Output ONLY the JSON object. Nothing else."
    )

    # Trim articles to avoid overloading context
    # Each article has title + abstract — keep top 5
    articles_trimmed = articles[:5]

    # Trim each abstract to 600 chars
    for art in articles_trimmed:
        if "abstract" in art and len(art["abstract"]) > 600:
            art["abstract"] = art["abstract"][:600] + "..."

    prompt = (
        f"Procedure denied: {denial_details.procedure_denied}\n"
        f"Denial reason: {denial_details.insurer_reason_snippet}\n\n"
        "PubMed articles:\n"
        f"{json.dumps(articles_trimmed, indent=2)}\n\n"
        "Now output the JSON object matching the schema:"
    )

    logger.info("[Clinician] Sending articles to Ollama for synthesis...")

    raw = client.generate(
        prompt=prompt,
        system=sys_instr,
        temperature=0.1,
        max_tokens=1024,
        json_mode=True,
    )

    if not raw:
        logger.error("[Clinician] Ollama returned empty response.")
        return EvidenceList(root=[])

    logger.debug(f"[Clinician] Raw response: {raw[:300]}")

    # ── Parse response ────────────────────────────────────────────────────
    clean = _clean_json(raw)

    # Primary parse
    try:
        evidence = EvidenceList.model_validate_json(clean)
        logger.info(f"[Clinician] Evidence synthesized. Count: {len(evidence.root)}")
        return evidence
    except Exception:
        logger.warning("[Clinician] Strict parse failed, attempting recovery.")

    # Recovery parse
    recovered = _extract_first_json(clean)
    if not recovered:
        logger.error("[Clinician] Could not recover JSON.")
        return EvidenceList(root=[])

    # Handle both {"root": [...]} and plain [...] shapes
    if isinstance(recovered, list):
        recovered = {"root": recovered}

    try:
        evidence = EvidenceList.model_validate(recovered)
        logger.info(f"[Clinician] Recovered. Count: {len(evidence.root)}")
        return evidence
    except Exception as e:
        logger.error(f"[Clinician] Recovery failed: {e}")
        return EvidenceList(root=[])