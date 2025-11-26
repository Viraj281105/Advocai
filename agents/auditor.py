# agents/auditor.py
# UPDATED: Improved robustness for structured JSON extraction from Gemini,
# defensive parsing, schema precomputation, context reduction, and better
# diagnostics when the LLM returns partial/invalid JSON.

from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import json
from tools.document_reader import extract_text_from_document
from typing import ClassVar, List, Optional, Dict, Any
import re
import logging

logger = logging.getLogger("AuditorAgent")
logger.setLevel(logging.INFO)


# ===========================================================
# 1. Pydantic Model (Structured Memory for Downstream Agents)
# ===========================================================
class StructuredDenial(BaseModel):
    """The structured memory produced by the Auditor Agent."""

    _SCHEMA: ClassVar[dict] = {}

    denial_code: str = Field(..., description="Primary Claim Adjustment Reason Code (e.g., CO-50, CO-16).")
    insurer_reason_snippet: str = Field(..., description="Exact quoted reason from insurer (the core justification for the denial).")
    policy_clause_text: str = Field(..., description="Exact policy clause cited for denial justification (e.g., the 'experimental/unproven' definition section).")
    procedure_denied: str = Field(..., description="The procedure or service that was denied.")
    confidence_score: float = Field(..., description="Confidence score 0.0–1.0 for extraction, reflecting LLM certainty.")
    raw_evidence_chunks: List[str] = Field(
        default_factory=list,
        description="Extracted raw chunks from denial & policy documents for matching by Judge Agent."
    )


# Precompute and store JSON schema for use in system prompts / response_schema.
if not StructuredDenial._SCHEMA:
    try:
        StructuredDenial._SCHEMA = StructuredDenial.model_json_schema()
    except Exception:
        StructuredDenial._SCHEMA = {}


# -------------------------------------------------------------------
# Helper: Search for the denial clause in the full policy text
# -------------------------------------------------------------------
def find_relevant_policy_snippet(full_policy_text: str) -> str:
    """Heuristically searches for key policy terms related to exclusions.

    If a strong match isn't found, returns a trimmed excerpt (up to 4000 chars).
    """
    policy_keywords = [
        "EXCLUSIONS AND LIMITATIONS",
        "EXCLUSIONS",
        "EXPERIMENTAL",
        "INVESTIGATIVE",
        "UNPROVEN",
        "CLINICAL TRIAL",
        "NOT COVERED",
    ]

    best_snippet = ""
    for keyword in policy_keywords:
        # look for keyword and return a surrounding paragraph block
        # capture up to 1500 characters before and after to keep context but reduce size
        pattern = r"(.{0,1500}" + re.escape(keyword) + r".{0,1500})"
        match = re.search(pattern, full_policy_text, re.IGNORECASE | re.DOTALL)
        if match:
            best_snippet = match.group(1)
            break

    if best_snippet:
        # attempt to shrink to the nearest paragraph boundaries
        paras = re.split(r"\n{2,}|\r\n{2,}", best_snippet)
        for p in paras:
            if re.search(r"EXPERIMENTAL|INVESTIGATIVE|UNPROVEN|EXCLUSIONS|NOT COVERED|CLINICAL TRIAL", p, re.IGNORECASE):
                return p.strip()
        return best_snippet.strip()

    # fallback: first 4000 characters (trim trailing incomplete words)
    return full_policy_text[:4000].rsplit("\n", 1)[0].strip()


# ===========================================================
# 2. Auditor Agent
# ===========================================================
def run_auditor_agent(client: genai.Client, denial_path: str, policy_path: str) -> Optional[StructuredDenial]:
    """
    Extracts text from denial letter and policy, then uses Gemini to produce
    a strict JSON structured denial object based on the Pydantic model.

    Returns StructuredDenial or None on failure. This function is intentionally
    defensive and will attempt to recover from partial/invalid JSON outputs.
    """
    logger.info("[Auditor] Extracting text from documents...")

    # ------------------------------
    # STEP 1: Extract raw text
    # ------------------------------
    denial_text_result = extract_text_from_document(denial_path)
    policy_text_result = extract_text_from_document(policy_path)

    if denial_text_result.get("error") or policy_text_result.get("error"):
        logger.error("[Auditor Error] Document reading tool failed: %s",
                     denial_text_result.get('error') or policy_text_result.get('error'))
        return None

    denial_text = denial_text_result.get("full_text_content", "")
    full_policy_text = policy_text_result.get("full_text_content", "")

    if not denial_text.strip() or not full_policy_text.strip():
        logger.error("[Auditor Error] One or both documents appear empty.")
        return None

    # ------------------------------
    # STEP 1.5: Prep raw evidence chunks (Uses ALL segments for Judge Agent)
    # ------------------------------
    raw_chunks = []
    raw_chunks.extend(denial_text_result.get("segments", []))
    raw_chunks.extend(policy_text_result.get("segments", []))
    raw_chunks = [c.strip() for c in raw_chunks if c and len(c.strip()) > 30][:24]

    logger.info("[Auditor] Generated %d evidence chunks for Judge Agent", len(raw_chunks))

    # ------------------------------
    # STEP 2: Build UNIFIED CONTEXT (REDUCED POLICY TEXT)
    # ------------------------------
    relevant_policy_snippet = find_relevant_policy_snippet(full_policy_text)

    full_context = (
        "--- DENIAL LETTER TEXT (REQUIRED) ---\n"
        f"{denial_text}\n\n"
        "--- POLICY EXCLUSION SECTION (REQUIRED FOR POLICY CLAUSE TEXT) ---\n"
        f"{relevant_policy_snippet}\n"
    )

    # ------------------------------
    # STEP 3: LLM for structured extraction
    # ------------------------------
    # Use the precomputed schema; still provide a human-readable schema in system instruction
    readable_schema = json.dumps(StructuredDenial._SCHEMA, indent=2)

    system_instruction = (
        "You are the Auditor Agent. Your job is to extract health insurance "
        "denial information and return STRICT JSON ONLY – no markdown, "
        "no code fences, no explanations.\n\n"
        "Follow exactly this schema and ensure the output is valid JSON. "
        "If a field is not present in the source documents, set it to an empty string "
        "or 0.0 for numeric confidence.\n\n"
        "SCHEMA:\n"
        f"{readable_schema}\n\n"
        "IMPORTANT:\n"
        "- The 'raw_evidence_chunks' field in the output MUST be an empty list (the agent should not populate it).\n"
        "- DO NOT hallucinate. Only extract data present in the text.\n"
        "- Extract the shortest possible snippet that contains the full justification for 'policy_clause_text'.\n"
    )

    user_prompt = (
        "Extract all required data fields from the following text. Return ONLY valid JSON.\n\n"
        f"{full_context}"
    )

    logger.info("[Auditor] Sending context to Gemini for structured extraction...")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=StructuredDenial._SCHEMA,
                max_output_tokens=2048,
                temperature=0.0,
            ),
        )

        # defensive: try to extract text from response
        raw_text = None
        if hasattr(response, 'text') and response.text:
            raw_text = response.text.strip()
        elif hasattr(response, 'candidates') and response.candidates:
            # Gemini sometimes nests candidates -> extract first candidate text
            try:
                # some SDKs place content in candidates[0].content[0].text
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    # join all content parts that are text-like
                    parts = [getattr(c, 'text', str(c)) for c in candidate.content]
                    raw_text = "\n".join(parts).strip()
                else:
                    raw_text = getattr(candidate, 'text', None)
            except Exception:
                raw_text = None

        if not raw_text:
            logger.error("[Auditor Error] LLM returned empty or None text response, likely due to safety filters or API error.")
            # surface safety ratings if available for debugging
            if hasattr(response, 'candidates') and response.candidates and hasattr(response.candidates[0], 'safety_ratings'):
                logger.error("Safety ratings: %s", response.candidates[0].safety_ratings)
            return None

        # First attempt: strict pydantic JSON parsing
        try:
            structured_output = StructuredDenial.model_validate_json(raw_text)
        except Exception as primary_err:
            # If primary parse fails, try to recover by extracting the first JSON object from raw_text
            logger.warning("[Auditor Warning] Primary JSON parse failed: %s", primary_err)
            json_obj = _extract_json_object_from_text(raw_text)
            if not json_obj:
                logger.error("[Auditor Error] Could not extract a valid JSON object from LLM output. Raw start: %s", raw_text[:300])
                # Save raw for debugging
                try:
                    with open("data/output/auditor_raw_response.txt", "w", encoding="utf-8") as fh:
                        fh.write(raw_text)
                except Exception:
                    pass
                return None
            try:
                structured_output = StructuredDenial.model_validate(json_obj)
            except Exception as second_err:
                logger.error("[Auditor Error] Secondary parse with extracted JSON failed: %s", second_err)
                logger.error("Extracted JSON (start): %s", json.dumps(json_obj)[:400])
                # Save extracted JSON for debugging
                try:
                    with open("data/output/auditor_extracted_json_debug.json", "w", encoding="utf-8") as fh:
                        fh.write(json.dumps(json_obj, indent=2))
                except Exception:
                    pass
                return None

        # Overwrite the raw_evidence_chunks with the local data (Judge will use these)
        structured_output.raw_evidence_chunks = raw_chunks

        logger.info("[Auditor Success] Structured Denial Object created.")
        logger.info("[Auditor Info] Denial Code: %s", structured_output.denial_code)
        logger.info("[Auditor Info] Procedure: %s", structured_output.procedure_denied)

        return structured_output

    except Exception as e:
        logger.exception("[Auditor Error] Failed to generate structured output: %s", e)
        try:
            raw_text_debug = str(getattr(response, 'text', 'N/A'))
        except Exception:
            raw_text_debug = 'N/A'
        logger.error("Raw response text (start): %s", raw_text_debug[:400])
        # save raw response for diagnosis
        try:
            with open("data/output/auditor_raw_response.txt", "w", encoding="utf-8") as fh:
                fh.write(raw_text_debug)
        except Exception:
            pass
        return None


# -------------------------------------------------------------------
# Utility: extract the first JSON object from a body of text using a simple brace-matching approach
# -------------------------------------------------------------------
def _extract_json_object_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Finds the first balanced JSON object in text and returns a parsed dict.

    This is intentionally tolerant to trailing commentary before/after the JSON block.
    """
    if not text or '{' not in text:
        return None

    # find first opening brace
    start_idx = text.find('{')
    stack = []
    end_idx = None
    for i in range(start_idx, len(text)):
        ch = text[i]
        if ch == '{':
            stack.append('{')
        elif ch == '}':
            if stack:
                stack.pop()
                if not stack:
                    end_idx = i
                    break
    if end_idx is None:
        return None

    candidate = text[start_idx:end_idx+1]

    # Sometimes LLMs include trailing commas or unquoted keys. We try a safe json.loads first.
    try:
        return json.loads(candidate)
    except Exception:
        # Attempt simple cleanup: remove trailing commas before closing braces/brackets
        cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
        try:
            return json.loads(cleaned)
        except Exception:
            # give up gracefully
            return None


# If this module is executed directly (for quick local testing), provide a tiny harness
if __name__ == '__main__':
    import os
    # quick smoke test (requires proper Google GenAI client configuration in environment)
    client = genai.Client()
    # replace with local test files if available
    denial_path = os.environ.get('TEST_DENIAL_PATH', 'tests/sample_denial.pdf')
    policy_path = os.environ.get('TEST_POLICY_PATH', 'tests/sample_policy.pdf')
    out = run_auditor_agent(client, denial_path, policy_path)
    if out:
        print('Parsed structured denial:')
        # model_dump gives a dict in pydantic v2; pretty print via json.dumps
        try:
            obj = out.model_dump()
            print(json.dumps(obj, indent=2))
        except Exception:
            # fallback to model_dump_json without indent (safe for pydantic v2)
            try:
                print(out.model_dump_json())
            except Exception:
                print(repr(out))
    else:
        print('No output (see logs).')
