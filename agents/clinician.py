# agents/clinician.py

from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional 
import json

# Import the StructuredDenial model from the Auditor
from .auditor import StructuredDenial 
# Import the custom tool
from tools.pubmed_search import pubmed_search 

# --- CONFIGURATION ---
CLINICIAN_MODEL = "gemini-2.5-flash" # Consistent model for stability

# --- 1. Pydantic Models for Output ---
class ClinicalEvidence(BaseModel):
    """A single piece of synthesized evidence from a medical abstract."""
    article_title: str = Field(description="The title of the primary supporting article.")
    summary_of_finding: str = Field(description="A concise summary (2-3 sentences) of the finding that supports the denied procedure.")
    pubmed_id: str = Field(description="The PubMed ID or source reference for the finding.")

class EvidenceList(BaseModel):
    """The root model containing a list of all clinical evidence found."""
    root: List[ClinicalEvidence]


# --- 2. Clinician Agent Function ---
def run_clinician_agent(client: genai.Client, denial_details: StructuredDenial) -> Optional[EvidenceList]:
    """
    The Clinician Agent workflow. It takes structured denial data, uses the
    pubmed_search tool, and synthesizes the findings into a structured list.
    """
    print("\n[Clinician Status] Preparing search query...") 
    
    # Base the search query on the Auditor's output
    search_query = (
        f"medical necessity of {denial_details.procedure_denied} "
        f"clinical trial evidence against {denial_details.denial_code}"
    )
    
    system_instruction = (
        "You are the Clinician Agent, a specialized medical researcher. "
        "To successfully complete your task, you **MUST FIRST CALL THE 'pubmed_search' TOOL** with the best possible query based on the 'procedure denied' and 'insurer reason snippet'. "
        "You may not provide a final answer or synthesis until after the tool output has been received."
    )
    
    print(f"[Clinician Status] LLM is reasoning and calling tool with query: {search_query[:50]}...")
    
    # --- STEP 1: LLM Reasoning and Tool Call (FIXED CONFIG) ---
    try:
        response = client.models.generate_content(
            model=CLINICIAN_MODEL,
            contents=[
                # Prompt the model to call the search tool
                f"Using the provided denial details, find clinical evidence to support the procedure: {search_query}",
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                # CRITICAL FIX: The LLM must output a function call, so we only pass the tools.
                # We remove the response_mime_type/schema from this first call!
                tools=[pubmed_search],
            )
        )
        
        # --- STEP 2: Execute the Tool Call (If Suggested) ---
        if not response.function_calls:
            print("[Clinician Warning] LLM did not suggest a tool call.")
            print("Reasoning: ", response.text)
            return None

        # Execute the function call suggested by the model (assuming only one for simplicity)
        tool_call = response.function_calls[0]
        tool_function = tool_call.name
        tool_args = dict(tool_call.args)
        
        # Map the tool name to the actual function
        if tool_function == "pubmed_search":
            tool_output = pubmed_search(**tool_args)
        else:
            raise ValueError(f"Unknown tool call: {tool_function}")

        # --- STEP 3: Return Tool Results to LLM for Synthesis ---
        print("[Clinician Status] Tool executed. Sending results back to LLM for synthesis...")
        
        second_response = client.models.generate_content(
            model=CLINICIAN_MODEL, 
            contents=[
                response.candidates[0].content, # The original tool call request
                types.Content(
                    role="function",
                    parts=[
                        types.Part.from_function_response(
                            name=tool_function,
                            response=tool_output, # The actual data from PubMed
                        )
                    ]
                )
            ],
            # This second call REQUIRES structured output to generate EvidenceList
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=EvidenceList.model_json_schema(),
            )
        )
        
        # --- STEP 4: Final Structured Output ---
        final_evidence = EvidenceList.model_validate_json(second_response.text)
        print("[Clinician Success] Clinical Evidence Synthesized.")
        return final_evidence

    except Exception as e:
        print(f"[Clinician Error] Failed during workflow: {e}")
        return None

if __name__ == '__main__':
    # Testing is done in main.py
    pass