# agents/clinician.py (FINAL, ROBUST FIX for SDK Conflict)

from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Union
import json
import re
import logging

from .auditor import StructuredDenial
from tools.pubmed_search import pubmed_search  # raw function

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CLINICIAN_MODEL = "gemini-2.5-flash"


# ============================================================
# 1. Pydantic Models
# ============================================================
class ClinicalEvidence(BaseModel):
    article_title: str
    summary_of_finding: str
    pubmed_id: str


class EvidenceList(BaseModel):
    root: List[ClinicalEvidence]


# ============================================================
# Helper Functions
# ============================================================
def _clean_json_text(s: str) -> str:
    if not s:
        return s
    s = s.strip()
    s = re.sub(r"```(?:json)?\s*", "", s)
    s = s.replace("```", "")
    return s.strip()


def _get_clean_search_query(denial_details: StructuredDenial) -> str:
    reason = denial_details.insurer_reason_snippet.lower()
    keywords = []

    if "asymptomatic" in reason:
        keywords.append("asymptomatic")

    if "experimental" in reason or "unproven" in reason:
        keywords.append("clinical utility established")

    base_query = f"{denial_details.procedure_denied} clinical efficacy"

    if keywords:
        return f"{base_query} {' '.join(keywords)}"

    return base_query


# ============================================================
# Clinician Agent
# ============================================================
def run_clinician_agent(client: genai.Client, denial_details: StructuredDenial) -> Optional[EvidenceList]:
    """
    1. LLM chooses best PubMed search query
    2. Actual tool executes pubmed_search()     (real API call)
    3. LLM synthesizes structured JSON EvidenceList
    """
    print("\n[Clinician Status] Preparing search query...")

    initial_query = _get_clean_search_query(denial_details)

    system_instruction = (
        "You are the Clinician Agent, a specialized medical researcher.\n"
        "Goal: Identify peer-reviewed articles showing the procedure is safe, effective, "
        "clinically validated, and NOT experimental.\n\n"
        "Instructions:\n"
        "1. Call the 'pubmed_search' TOOL using the best possible query.\n"
        "2. After tool output is returned, synthesize results into valid JSON "
        "following the EvidenceList schema.\n\n"
        f"Schema:\n{json.dumps(EvidenceList.model_json_schema(), indent=2)}\n"
    )

    # ============================================================
    # Step 1 — LLM chooses the PubMed search query
    # ============================================================
    tool_prompt = f"""
The denied procedure is: {denial_details.procedure_denied}
The insurer's stated reason: "{denial_details.insurer_reason_snippet}"
Suggested baseline query: "{initial_query}"

Call the 'pubmed_search' tool now using your optimized final query.
"""

    print(f"[Clinician Status] LLM is reasoning and calling tool with initial query: {initial_query}...")

    try:
        response = client.models.generate_content(
            model=CLINICIAN_MODEL,
            contents=[tool_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[pubmed_search],
            ),
        )

        final_query = initial_query
        tool_calls = getattr(response, "function_calls", [])

        if tool_calls:
            call = tool_calls[0]
            if call.name == "pubmed_search":
                final_query = call.args.get("query", initial_query)
            else:
                print(f"[Clinician Warning] Unexpected tool: {call.name}. Using fallback query.")
        else:
            print("[Clinician Warning] No tool call suggested. Using fallback query.")

    except Exception as e:
        print(f"[Clinician Error] LLM failed before tool stage: {e}")
        return None

    # ============================================================
    # Step 2 — Execute the tool
    # ============================================================
    try:
        print(f"[Clinician Status] Executing tool 'pubmed_search' with query: {final_query}")
        raw_tool_output = pubmed_search(query=final_query)

        if not isinstance(raw_tool_output, str) or raw_tool_output.startswith("E"):
            print("[Clinician Warning] PubMed search returned invalid data.")
            return None

    except Exception as e:
        print(f"[Clinician Error] PubMed tool execution failed: {e}")
        return None

    # ============================================================
    # Step 3 — LLM synthesizes EvidenceList JSON
    # ============================================================
    print("[Clinician Status] Tool executed. Sending results back to LLM for synthesis...")

    synthesis_prompt = (
        "Synthesize the following PubMed abstracts into the EvidenceList JSON format.\n"
        "The summary_of_finding must clearly state **why this procedure is not experimental**.\n\n"
        f"TOOL OUTPUT:\n{raw_tool_output}"
    )

    try:
        second = client.models.generate_content(
            model=CLINICIAN_MODEL,
            contents=[synthesis_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=EvidenceList.model_json_schema(),
            ),
        )

        if not hasattr(second, "text") or not second.text:
            print("[Clinician Error] LLM returned no structured JSON.")
            return None

        clean_json = _clean_json_text(second.text)
        evidence = EvidenceList.model_validate_json(clean_json)

        print("[Clinician Success] Clinical Evidence Synthesized.")
        return evidence

    except Exception as e:
        print(f"[Clinician Error] Synthesis failed: {e}")
        logger.exception("Clinician synthesis failed", exc_info=True)
        return None
