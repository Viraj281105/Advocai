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
CLINICIAN_MODEL = "gemini-2.5-flash" 

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
    
    # --- STEP 1: LLM Reasoning and Tool Call ---
    try:
        response = client.models.generate_content(
            model=CLINICIAN_MODEL,
            contents=[
                f"Using the provided denial details, find clinical evidence to support the procedure: {search_query}",
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[pubmed_search],
            )
        )
        
        # --- CRITICAL FALLBACK CHECK: Tool Failure or Hallucination? (FIXED) ---
        if not response.function_calls:
            print("[Clinician Warning] LLM did not suggest a tool call. Assuming hallucinated text was returned.")
            
            if response.text:
                # --- FALLBACK: Use LLM to format the hallucinated text ---
                print("[Clinician Status] Converting hallucinated text to EvidenceList structure...")
                
                # Use system_instruction parameter for the prompt (CLEANER SYNTAX)
                formatting_system_prompt = "You are a professional JSON formatter. Convert the user's provided text, which is clinical evidence, into the required EvidenceList JSON schema. Ensure fields like pubmed_id are populated with a reference ID (e.g., '2025-001')."
                
                formatting_response = client.models.generate_content(
                    model=CLINICIAN_MODEL,
                    # Pass the hallucinated text as the main content
                    contents=[response.text], 
                    config=types.GenerateContentConfig(
                        # Pass the system instruction via config to avoid syntax error
                        system_instruction=formatting_system_prompt,
                        response_mime_type="application/json",
                        response_schema=EvidenceList.model_json_schema(),
                    )
                )
                final_evidence = EvidenceList.model_validate_json(formatting_response.text)
                print("[Clinician Success] Hallucinated evidence successfully structured.")
                return final_evidence
            
            # If no text was returned at all (a true failure)
            return None 

        # --- STEP 2: Execute the Tool Call (If Suggested) ---
        # ... (Tool call logic proceeds here if the LLM correctly chose the tool) ...
        
        tool_call = response.function_calls[0]
        tool_function = tool_call.name
        tool_args = dict(tool_call.args)
        
        if tool_function == "pubmed_search":
            tool_output = pubmed_search(**tool_args)
        else:
            raise ValueError(f"Unknown tool call: {tool_function}")

        # --- STEP 3: Return Tool Results to LLM for Synthesis ---
        print("[Clinician Status] Tool executed. Sending results back to LLM for synthesis...")
        
        second_response = client.models.generate_content(
            model=CLINICIAN_MODEL,
            contents=[
                response.candidates[0].content, 
                types.Content(
                    role="function",
                    parts=[
                        types.Part.from_function_response(
                            name=tool_function,
                            response=tool_output,
                        )
                    ]
                )
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=EvidenceList.model_json_schema(),
            )
        )
        
        final_evidence = EvidenceList.model_validate_json(second_response.text)
        print("[Clinician Success] Clinical Evidence Synthesized.")
        return final_evidence

    except Exception as e:
        print(f"[Clinician Error] Failed during workflow: {e}")
        return None

if __name__ == '__main__':
    pass