# main.py

import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import all three agents and their required Pydantic models
from agents.auditor import run_auditor_agent, StructuredDenial
from agents.clinician import run_clinician_agent, EvidenceList
from agents.barrister import run_barrister_agent # Final agent import

# --- CONFIGURATION ---
MODEL_NAME = "gemini-2.5-pro" # Use the fast model for rapid development and testing

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

    print("\n--- Auditor Agent SUCCESS: Structured Output (Memory) ---")
    print(structured_denial_output.model_dump_json(indent=2))
    # -----------------------------------------------------------
    
    # 2. START THE CLINICIAN AGENT (Second Step)
    print("\n[STEP 2: Clinician Agent] Starting medical evidence search...")

    clinical_evidence: EvidenceList = run_clinician_agent(client=client, denial_details=structured_denial_output)

    if not clinical_evidence:
        print("--- Workflow Halted --- Clinician Agent failed to find evidence.")
        return

    print("\n--- Clinician Agent SUCCESS: Structured Evidence Output ---")
    print(clinical_evidence.model_dump_json(indent=2))
    # -----------------------------------------------------------
    
    # 3. START THE BARRISTER AGENT (Third Step)
    print("\n[STEP 3: Barrister Agent] Starting final appeal drafting...")
    
    final_appeal_text = run_barrister_agent(
        client=client, 
        denial_details=structured_denial_output,
        clinical_evidence=clinical_evidence
    )

    if not final_appeal_text:
        print("--- Workflow Halted --- Barrister Agent failed to generate appeal.")
        return
        
    print("\n--- Barrister Agent SUCCESS: FINAL APPEAL LETTER ---")
    print("\n" + "="*80)
    print(final_appeal_text)
    print("="*80)

    print("\n✅ --- Advocai Workflow Complete ---")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default to Case 1 if no argument is provided
        case_id = "case_1" 
    else:
        # Get the case ID from the command line (e.g., 'case_2')
        case_id = sys.argv[1] 

    # --- Construct paths based on the dynamic case_id ---
    DENIAL_PATH = f"data/input/denial_{case_id}.pdf"
    POLICY_PATH = f"data/input/policy_{case_id}.pdf"

    print(f"Loading Test Case: {case_id}...")

    if not os.path.exists(DENIAL_PATH) or not os.path.exists(POLICY_PATH):
        print(f"🚨 CRITICAL ERROR: Input files not found for case ID: {case_id}")
        print(f"Expected files: {DENIAL_PATH} and {POLICY_PATH}")
    else:
        # Pass both dynamic paths to the orchestrator
        orchestrate_advocai_workflow(DENIAL_PATH, POLICY_PATH)