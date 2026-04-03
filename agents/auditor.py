# agents/auditor.py — Auditor Agent (Local Ollama)
from pydantic import BaseModel, Field
from tools.document_reader import extract_text_from_document
from typing import List, Optional, Dict, Any, ClassVar
import re
import json
import logging

logger = logging.getLogger("AuditorAgent")
logger.setLevel(logging.INFO)


# ============================================================
# STRUCTURED DENIAL MODEL
# ============================================================
class StructuredDenial(BaseModel):
    """Auditor Agent → unified structured memory object."""
    _SCHEMA: ClassVar[dict] = {}

    denial_code: str
    insurer_reason_snippet: str
    policy_clause_text: str
    procedure_denied: str
    confidence_score: float
    raw_evidence_chunks: List[str] = Field(default_factory=list)


# cache schema
if not StructuredDenial._SCHEMA:
    StructuredDenial._SCHEMA = StructuredDenial.model_json_schema()


# ============================================================
# HELPERS
# ============================================================
def find_relevant_policy_snippet(full_policy_text: str) -> str:
    """Heuristic extraction of the exclusion/experimental sections."""
    keys = [
        "EXCLUSIONS", "EXCLUSIONS AND LIMITATIONS", "EXPERIMENTAL",
        "INVESTIGATIVE", "UNPROVEN", "CLINICAL TRIAL", "NOT COVERED"
    ]
    for kw in keys:
        m = re.search(
            rf".{{0,1500}}{re.escape(kw)}.{{0,1500}}",
            full_policy_text,
            re.IGNORECASE | re.DOTALL
        )
        if m:
            blk = m.group(0)
            paras = re.split(r"\n{2,}", blk)
            for p in paras:
                if any(k in p.upper() for k in keys):
                    return p.strip()
            return blk.strip()

    # fallback: first 4000 chars
    snippet = full_policy_text[:4000]
    return snippet.rsplit("\n", 1)[0].strip()


def extract_first_json(text: str) -> Optional[Dict[str, Any]]:
    """Balanced brace extraction for JSON recovery."""
    if not text:
        return None
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
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
# AUDITOR AGENT
# ============================================================
def run_auditor_agent(
    client,                 # OllamaClient from orchestrator/main.py
    denial_path: str,
    policy_path: str,
) -> Optional[StructuredDenial]:

    logger.info("[Auditor] Extracting text...")

    denial_res = extract_text_from_document(denial_path)
    policy_res = extract_text_from_document(policy_path)

    if denial_res.get("error") or policy_res.get("error"):
        logger.error(
            "Document reader failed: %s",
            denial_res.get("error") or policy_res.get("error")
        )
        return None

    denial_text = denial_res.get("full_text_content", "").strip()
    policy_text = policy_res.get("full_text_content", "").strip()

    if not denial_text or not policy_text:
        logger.error("One or both input docs empty.")
        return None

    # Evidence chunks — Judge consumes these
    segments = [
        seg.strip()
        for seg in (denial_res.get("segments", []) + policy_res.get("segments", []))
        if seg and len(seg.strip()) > 30
    ]
    evidence_chunks = segments[:24]
    logger.info(f"[Auditor] Evidence chunks: {len(evidence_chunks)}")

    # Identify key excerpt in policy
    policy_excerpt = find_relevant_policy_snippet(policy_text)

    # Truncate to avoid overloading context window
    # Mistral context = 32k tokens, ~4 chars per token → safe limit ~8000 chars each
    denial_text_trimmed = denial_text[:8000]
    policy_excerpt_trimmed = policy_excerpt[:4000]

    # ── System instruction ────────────────────────────────────────────────
    sys_instr = (
        "You are the Auditor Agent.\n"
        "Extract only facts from the insurer's denial letter and policy.\n"
        "Output STRICT JSON ONLY. No markdown. No explanation. No extra text.\n"
        "Follow this exact JSON schema:\n"
        f"{json.dumps(StructuredDenial._SCHEMA, indent=2)}\n\n"
        "Rules:\n"
        "- If a field is missing in source text, use empty string or 0.0.\n"
        "- Do NOT hallucinate.\n"
        "- 'raw_evidence_chunks' MUST be an empty list [].\n"
        "- Output ONLY the JSON object. Nothing else."
    )

    # ── User prompt ───────────────────────────────────────────────────────
    prompt = (
        "--- DENIAL LETTER ---\n"
        f"{denial_text_trimmed}\n\n"
        "--- RELEVANT POLICY EXCERPT ---\n"
        f"{policy_excerpt_trimmed}\n\n"
        "Now output the JSON object:"
    )

    logger.info("[Auditor] Sending prompt to Ollama...")

    raw = client.generate(
        prompt=prompt,
        system=sys_instr,
        temperature=0.0,
        max_tokens=1024,
        json_mode=True,     # tells Ollama to constrain output to valid JSON
    )

    if not raw:
        logger.error("[Auditor] Empty response from Ollama.")
        return None

    logger.debug(f"[Auditor] Raw response: {raw[:300]}")

    # ── Primary parse ─────────────────────────────────────────────────────
    try:
        sd = StructuredDenial.model_validate_json(raw)
    except Exception:
        logger.warning("[Auditor] Strict JSON parse failed, attempting recovery.")
        recovered = extract_first_json(raw)
        if not recovered:
            logger.error("[Auditor] Could not recover JSON from response.")
            logger.error(f"[Auditor] Raw was: {raw[:500]}")
            return None
        try:
            sd = StructuredDenial.model_validate(recovered)
        except Exception as e:
            logger.error(f"[Auditor] Recovery JSON invalid: {e}")
            return None

    # Overwrite with evidence chunks from local extraction
    sd.raw_evidence_chunks = evidence_chunks

    logger.info("[Auditor] SUCCESS — Structured denial created.")
    logger.info(f"[Auditor] Denial Code → {sd.denial_code}")
    logger.info(f"[Auditor] Procedure   → {sd.procedure_denied}")
    logger.info(f"[Auditor] Confidence  → {sd.confidence_score}")

    return sd