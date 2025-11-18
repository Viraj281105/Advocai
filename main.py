# main.py

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import the custom tools we just created
from tools.pubmed_search import pubmed_search
from tools.document_reader import extract_text_from_document

# --- CONFIGURATION ---
MODEL_NAME = "gemini-2.5-pro" # Use Pro for complex reasoning and tool-use

def initialize_gemini_client():
    """Initializes the Gemini client and ensures environment is set up."""
    # The client automatically picks up GEMINI_API_KEY from environment variables
    # (loaded by python-dotenv)
    try:
        client = genai.Client()
        return client
    except Exception as e:
        print(f"FATAL: Failed to initialize Gemini Client. Check GEMINI_API_KEY. Error: {e}")
        return None

def orchestrate_advocai_workflow(pdf_path: str):
    """
    Runs the full sequential Advocai workflow:
    Auditor -> Clinician -> Barrister
    """
    print("--- Advocai Workflow Initiated ---")
    load_dotenv()
    client = initialize_gemini_client()
    
    if not client:
        return

    # 1. DEFINE TOOLS: Register the Python functions as tools for the model
    available_tools = [pubmed_search, extract_text_from_document]

    # 2. START THE AUDITOR AGENT (First Step)
    initial_prompt = f"""
    You are the Auditor Agent. Your task is to analyze the following two documents
    (a Denial Letter and a Policy Document) using the 'extract_text_from_document' tool
    and clearly identify two items: the exact Denial Code (e.g., 'C125') and the specific
    Policy Clause (by full text) the insurer is citing.

    Denial Letter Path: {pdf_path}
    Policy Document Path: data/input/sample_policy.pdf 
    """
    
    print("STATUS: Auditor Agent is analyzing documents...")
    
    # Example: Run the generation with the tools enabled
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[initial_prompt],
            config=types.GenerateContentConfig(
                tools=available_tools
            )
        )
        print("\n--- AUDITOR AGENT OUTPUT ---")
        print(response.text)
        
        # NOTE: The next step would pass this output to the Clinician Agent
        
    except Exception as e:
        print(f"An error occurred during content generation: {e}")


if __name__ == "__main__":
    # Create a placeholder file path for testing purposes
    TEST_PDF_PATH = "data/input/sample_denial.pdf"
    
    # Ensure test files exist for a successful run (even if they are empty)
    if not os.path.exists("data/input"):
        os.makedirs("data/input")
    if not os.path.exists(TEST_PDF_PATH):
        print(f"Creating placeholder file: {TEST_PDF_PATH}. Please place a real PDF here for testing.")
        with open(TEST_PDF_PATH, 'w') as f: f.write("Placeholder content for testing.")
    if not os.path.exists("data/input/sample_policy.pdf"):
        with open("data/input/sample_policy.pdf", 'w') as f: f.write("Placeholder policy.")
        
    orchestrate_advocai_workflow(TEST_PDF_PATH)