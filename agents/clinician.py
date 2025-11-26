# agents/clinician.py — Production-Ready, Crash-Proof Clinician Agent

from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
import json
import re
import logging

from .auditor import StructuredDenial
from tools.pubmed_search import pubmed_search

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CLINICIAN_MODEL = "gemini-2.5-flash"


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
    """Generate an intelligent default PubMed query."""
    reason = denial.insurer_reason_snippet.lower()
    tags = []

    if "asymptomatic" in reason:
        tags.append("asymptomatic")

    if "experimental" in reason or "unproven" in reason:
        tags.append("clinical utility established")

    base = f"{denial.procedure_denied} clinical efficacy"
    return base + " " + " ".join(tags) if tags else base


# ============================================================
# MAIN AGENT
# ============================================================
def run_clinician_agent(client: genai.Client, denial_details: StructuredDenial) -> EvidenceList:
    """
    SAFETY GUARANTEE:
      → ALWAYS returns EvidenceList (never None).
      → Even if PubMed fails or LLM fails.
    """

    print("\n[Clinician] Preparing initial search query...")
    initial_query = _derive_query(denial_details)

    # --------------------------------------------------------
    # STEP 1: Ask Gemini for the best PubMed search query
    # --------------------------------------------------------
    system_instruction = (
        "You are the Clinician Agent. Your job is to identify high-quality "
        "peer-reviewed evidence that the denied procedure is clinically effective, "
        "safe, and not experimental.\n\n"
        "You MUST call the 'pubmed_search' tool with the best search query.\n"
        "After the tool returns article abstracts, you will synthesize them into "
        "EvidenceList JSON according to the schema.\n"
    )

    tool_prompt = f"""
Denied Procedure: {denial_details.procedure_denied}
Insurer Reason: {denial_details.insurer_reason_snippet}

Baseline query: "{initial_query}"

Call the 'pubmed_search' tool with your final optimized query.
"""

    print(f"[Clinician] Asking Gemini to choose a query…")

    try:
        llm_first = client.models.generate_content(
            model=CLINICIAN_MODEL,
            contents=[tool_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[pubmed_search],        # function object
            ),
        )
        # --------------------------------------------------------
        # Correct extraction of function call for Gemini SDK
        # --------------------------------------------------------
        call = None
        try:
            parts = llm_first.candidates[0].content.parts
            for p in parts:
                if hasattr(p, "function_call") and p.function_call:
                    call = p.function_call
                    break
        except Exception:
            call = None

        if call and call.name == "pubmed_search":
            final_query = call.args.get("query", initial_query)
            print(f"[Clinician] Gemini selected query: {final_query}")
        else:
            print("[Clinician] No function_call detected. Falling back to baseline query.")
            final_query = initial_query


    except Exception as e:
        print(f"[Clinician ERROR] Failed to generate tool call: {e}")
        return EvidenceList(root=[])

    # --------------------------------------------------------
    # STEP 2: Execute PubMed Tool
    # --------------------------------------------------------
    print(f"[Clinician] Executing pubmed_search() with: {final_query}")

    try:
        articles = pubmed_search(final_query)

        if not isinstance(articles, list):
            print("[Clinician] PubMed returned invalid type → using empty evidence list.")
            articles = []

    except Exception as e:
        print(f"[Clinician ERROR] PubMed tool crashed: {e}")
        return EvidenceList(root=[])

    # If tool yielded nothing → still proceed with synthesis (LLM may produce helpful summary)
    if not articles:
        print("[Clinician] PubMed returned zero articles. Will synthesize empty evidence list.")

    # --------------------------------------------------------
    # STEP 3: Synthesize structured JSON with Gemini
    # --------------------------------------------------------
    synthesis_prompt = (
        "Synthesize the PubMed results into the EvidenceList schema.\n"
        "If no articles are available, return an empty list.\n\n"
        f"TOOL OUTPUT:\n{json.dumps(articles, indent=2)}"
    )

    print("[Clinician] Sending tool output to Gemini for synthesis…")

    try:
        llm_second = client.models.generate_content(
            model=CLINICIAN_MODEL,
            contents=[synthesis_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=EvidenceList.model_json_schema(),
            ),
        )

        raw_json = llm_second.text if hasattr(llm_second, "text") else None
        if not raw_json:
            print("[Clinician] LLM returned nothing. Using empty evidence list.")
            return EvidenceList(root=[])

        clean = _clean_json(raw_json)
        evidence = EvidenceList.model_validate_json(clean)

        print(f"[Clinician] Evidence synthesized. Count: {len(evidence.root)}")
        return evidence

    except Exception as e:
        print(f"[Clinician ERROR] Synthesis failed: {e}")
        logger.exception("Clinician synthesis error:")
        return EvidenceList(root=[])
