# agents/auditor.py

from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import json
from tools.document_reader import extract_text_from_document # Using absolute import from top-level package

# --- 1. Pydantic Model (The Structured Output/Memory) ---
class StructuredDenial(BaseModel):
    """
    The structured output model required from the Auditor Agent. 
    This is the memory passed to the Clinician Agent.
    """
    
    # Example: CO-50 (Non-Covered Service), CO-16 (Claim Lacks Information)
    denial_code: str = Field(
        ..., 
        description="The primary Claim Adjustment Reason Code (e.g., CO-50, PR-27). Find the exact code in the denial letter."
    )
    
    # The exact reason cited by the insurer, which may be one or two sentences.
    insurer_reason_snippet: str = Field(
        ..., 
        description="The exact quote from the denial letter explaining the denial."
    )
    
    # The relevant policy clause the insurer is invoking.
    policy_clause_text: str = Field(
        ..., 
        description="The specific text from the policy document used to justify the denial."
    )
    
    # A short, simple summary of the medical procedure that was denied.
    procedure_denied: str = Field(
        ..., 
        description="The procedure denied (e.g., 'MRI of the lumbar spine', 'Physical Therapy')."
    )
    
    # Confidence score for extraction.
    confidence_score: float = Field(
        ...,
        description="Your confidence level (0.0 to 1.0) that the extracted data is accurate."
    )


# --- 2. Auditor Agent Function ---
def run_auditor_agent(client: genai.Client, denial_path: str, policy_path: str) -> StructuredDenial | None:
    """
    The Auditor Agent workflow. It extracts raw text and uses Gemini 
    with Pydantic to structure the core denial reasons.
    """
    print("\n[Auditor Status] Extracting text from documents...")
    
    # --- STEP 1: Execute Tool Directly (Extract Raw Text) ---
    denial_text = extract_text_from_document(denial_path)
    policy_text = extract_text_from_document(policy_path)
    
    if denial_text.get("error") or policy_text.get("error"):
        print(f"[Auditor Error] Tool failed: {denial_text.get('error') or policy_text.get('error')}")
        return None

    # Concatenate the raw text for the LLM to process
    full_context = f"""
    --- DENIAL LETTER TEXT ---
    {denial_text['full_text_content']}
    
    --- POLICY DOCUMENT TEXT ---
    {policy_text['full_text_content']}
    """
    
    # --- STEP 2: LLM Reasoning and Structured Output (FIXED) ---
    system_instruction = (
        "You are the Auditor Agent, specialized in parsing complex health insurance documents. "
        "Your task is to analyze the provided denial letter and policy text and extract the "
        "required information into a strict JSON format based on the Pydantic schema."
    )
    
    user_prompt = f"Extract the denial details from the following context:\n\n{full_context}"
    
    print("[Auditor Status] Sending context to Gemini for structured extraction...")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            # We pass only the user content here.
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                # We pass the system instruction via config (the clean method)
                system_instruction=system_instruction, 
                # Crucial for structured output
                response_mime_type="application/json",
                response_schema=StructuredDenial.model_json_schema(),
            )
        )
        
        # Validate and parse the JSON output into the Pydantic object
        structured_output = StructuredDenial.model_validate_json(response.text)
        print("[Auditor Success] Structured Denial Object created.")
        return structured_output
    
    except Exception as e:
        print(f"[Auditor Error] Failed to generate structured output: {e}")
        print(f"Raw response text: {response.text if 'response' in locals() else 'N/A'}")
        return None

if __name__ == '__main__':
    # This block requires initializing the client in main.py, so testing is done there.
    pass