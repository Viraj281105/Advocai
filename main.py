# main.py

import os
import sys # Needed for reading command line arguments (case_id)
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import all three agents and their required Pydantic models
from agents.auditor import run_auditor_agent, StructuredDenial
from agents.clinician import run_clinician_agent, EvidenceList
from agents.barrister import run_barrister_agent

# --- CONFIGURATION ---
MODEL_NAME = "gemini-2.5-flash" 

def initialize_gemini_client():
    """Initializes the Gemini client and ensures environment is set up."""
    load_dotenv()
    try:
        client = genai.Client()
        return client
    except Exception as e:
        print(f"FATAL: Failed to initialize Gemini Client. Check GEMINI_API_KEY. Error: {e}")
        return None

def orchestrate_advocai_workflow(client: genai.Client, denial_path: str, policy_path: str, case_id: str):
    """
    Runs the full sequential Advocai workflow and saves the final output.
    """
    print("--- Advocai Workflow Initiated ---")

    # 1. START THE AUDITOR AGENT
    print("\n[STEP 1: Auditor Agent] Starting document parsing and structuring...")
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
    
    # 2. START THE CLINICIAN AGENT
    print("\n[STEP 2: Clinician Agent] Starting medical evidence search...")
    clinical_evidence: EvidenceList = run_clinician_agent(client=client, denial_details=structured_denial_output)

    if not clinical_evidence:
        print("--- Workflow Halted --- Clinician Agent failed to find evidence.")
        return

    print("\n--- Clinician Agent SUCCESS: Structured Evidence Output ---")
    print(clinical_evidence.model_dump_json(indent=2))
        
    # 3. START THE BARRISTER AGENT
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
    
    # 4. FINAL STEP: SAVE THE GENERATED FILE
    output_filename = f"appeal_{case_id}_{structured_denial_output.denial_code}.txt"
    output_path = os.path.join("data", "output", output_filename)
    
    # Ensure the output directory exists
    os.makedirs(os.path.join("data", "output"), exist_ok=True)

    try:
        # Save as .txt for easy viewing; you can convert to PDF later if needed
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_appeal_text)
        print(f"\n[SUCCESS] Final appeal saved to: {output_path}")
    except Exception as e:
        print(f"\n[FAILURE] Could not save appeal file: {e}")

    print("\n✅ --- Advocai Workflow Complete ---")


if __name__ == "__main__":
    client = initialize_gemini_client()
    if not client:
        sys.exit(1)
        
    # --- Check for a command line argument for the test case ID ---
    if len(sys.argv) < 2:
        case_id = "case_1" 
    else:
        case_id = sys.argv[1] 

    # --- Construct paths based on the dynamic case_id ---
    DENIAL_PATH = os.path.join("data", "input", f"denial_{case_id}.pdf")
    POLICY_PATH = os.path.join("data", "input", f"policy_{case_id}.pdf")

    print(f"Loading Test Case: {case_id}...")

    if not os.path.exists(DENIAL_PATH) or not os.path.exists(POLICY_PATH):
        print(f"🚨 CRITICAL ERROR: Input files not found for case ID: {case_id}")
        print(f"Expected files: {DENIAL_PATH} and {POLICY_PATH}")
    else:
        # Pass the client and all paths/IDs to the orchestrator
        orchestrate_advocai_workflow(client, DENIAL_PATH, POLICY_PATH, case_id)