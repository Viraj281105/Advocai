# main.py

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import the Auditor Agent and its required Pydantic model
from agents.auditor import run_auditor_agent, StructuredDenial

# --- CONFIGURATION ---
MODEL_NAME = "gemini-2.5-pro" # Using Pro for complex reasoning and structured output

def initialize_gemini_client():
    """Initializes the Gemini client and ensures environment is set up."""
    load_dotenv()
    try:
        # The client automatically picks up GEMINI_API_KEY from environment variables
        client = genai.Client()
        return client
    except Exception as e:
        print(f"FATAL: Failed to initialize Gemini Client. Check GEMINI_API_KEY. Error: {e}")
        return None

def orchestrate_advocai_workflow(denial_path: str, policy_path: str):
    """
    Runs the full sequential Advocai workflow: Auditor -> Clinician -> Barrister.
    """
    print("--- Advocai Workflow Initiated ---")
    client = initialize_gemini_client()
    
    if not client:
        return

    # 1. START THE AUDITOR AGENT (First Step)
    print("\n[STEP 1: Auditor Agent] Starting document parsing and structuring...")
    
    # Run the Auditor Agent and receive the Pydantic object
    structured_denial_output: StructuredDenial = run_auditor_agent(
        client=client,
        denial_path=denial_path,
        policy_path=policy_path
    )

    if not structured_denial_output:
        print("--- Workflow Halted --- Auditor Agent failed to produce structured data.")
        return

    # Display the structured memory object
    print("\n--- Auditor Agent SUCCESS: Structured Output (Memory) ---")
    print(structured_denial_output.model_dump_json(indent=2))
    print(f"Denial Code Extracted: {structured_denial_output.denial_code}")

    # -----------------------------------------------------------
    # 2. PLACEHOLDER: START THE CLINICIAN AGENT (Second Step)
    # -----------------------------------------------------------
    print("\n[STEP 2: Clinician Agent] Starting medical evidence search...")
    
    # The output from STEP 1 becomes the input for STEP 2
    # clinical_evidence = run_clinician_agent(client=client, denial_details=structured_denial_output)
    
    # if not clinical_evidence:
    #     print("--- Workflow Halted --- Clinician Agent failed to find evidence.")
    #     return
    
    # -----------------------------------------------------------
    # 3. PLACEHOLDER: START THE BARRISTER AGENT (Third Step)
    # -----------------------------------------------------------
    print("\n[STEP 3: Barrister Agent] Starting final appeal drafting...")
    
    # final_appeal_text = run_barrister_agent(client=client, all_evidence=clinical_evidence)

    print("\n--- Advocai Workflow Complete ---")


if __name__ == "__main__":
    # --- File Paths (Ensure these PDFs exist in data/input) ---
    DENIAL_PATH = "data/input/sample_denial.pdf"
    POLICY_PATH = "data/input/sample_policy.pdf"
    
    # NOTE: Assuming you have now placed real PDF files in data/input for testing.
    if not os.path.exists(DENIAL_PATH) or not os.path.exists(POLICY_PATH):
        print("🚨 CRITICAL ERROR: Please place real PDF files named 'sample_denial.pdf' and 'sample_policy.pdf' in the data/input folder.")
        print("Workflow cannot proceed without valid input documents.")
    else:
        # Pass both paths to the orchestrator
        orchestrate_advocai_workflow(DENIAL_PATH, POLICY_PATH)