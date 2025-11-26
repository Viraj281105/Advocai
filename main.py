# main.py (FINAL FIXED ORCHESTRATOR)
import os
import sys
import json
import logging
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel
from typing import Any

# Agent imports
from agents.auditor import run_auditor_agent, StructuredDenial
from agents.clinician import run_clinician_agent, EvidenceList
from agents.barrister import run_barrister_agent
from agents.regulatory import run_regulatory_agent
from agents.judge import run_judge_agent

# --- CONFIGURATION & LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - Orchestrator - %(levelname)s - %(message)s")
logger = logging.getLogger("AdvocaiOrchestrator")


def initialize_gemini_client() -> genai.Client | None:
    """
    Initializes the Gemini / genai client.
    - Loads .env
    - Logs presence/absence of common API keys but does not hard-fail if not present,
      because ADC or other auth may be available.
    """
    load_dotenv()
    env_candidates = ["GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY"]
    found = [k for k in env_candidates if os.getenv(k)]
    if not found:
        logger.warning(
            "No common API key env vars found (GEMINI_API_KEY / GOOGLE_API_KEY / OPENAI_API_KEY). "
            "genai.Client() may still initialize via ADC/service account; proceeding to instantiate client."
        )
    try:
        client = genai.Client()
        logger.info("genai.Client() initialized successfully.")
        return client
    except Exception as e:
        logger.fatal(f"Failed to initialize genai.Client(): {e}")
        return None


def save_json_to_file(obj: Any, path: str) -> bool:
    """
    Save a Pydantic BaseModel, dict/list, or str to a file in a safe, robust way.
    - BaseModel -> obj.model_dump() then json.dump
    - dict/list -> json.dump
    - str -> try to parse JSON first; if not JSON, write as plain text
    Returns True on success, False on failure.
    """
    try:
        # Ensure parent directory exists (if path has a directory component)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        # Pydantic model handling (pydantic v2)
        if isinstance(obj, BaseModel):
            data = obj.model_dump()
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
            return True

        # If it's already a dict/list, write JSON
        if isinstance(obj, (dict, list)):
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(obj, fh, indent=2, ensure_ascii=False)
            return True

        # If it's a string: try to detect JSON
        if isinstance(obj, str):
            # Strip common whitespace noise
            s = obj.strip()
            # Try parse as JSON
            try:
                parsed = json.loads(s)
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(parsed, fh, indent=2, ensure_ascii=False)
                return True
            except json.JSONDecodeError:
                # Not JSON: save as plain text (useful for barrister_output.txt)
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(obj)
                return True
            except Exception as e:
                logger.warning("Unexpected error while parsing string to JSON: %s", e)
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(obj)
                return True

        # Fallback: try to JSON-serialize unknown object
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, ensure_ascii=False)
        return True

    except Exception as e:
        logger.error(f"Failed to save file {path}: {e}", exc_info=True)
        return False


def orchestrate_advocai_workflow(client: genai.Client, denial_path: str, policy_path: str, case_id: str):
    """
    Runs the full Advocai workflow:
      1) Auditor -> structured denial
      2) Clinician -> medical evidence
      3) Regulatory -> compliance analysis
      4) Barrister -> appeal drafting
      5) Judge -> scoring & report
    """
    logger.info("--- Advocai Workflow Initiated ---")
    case_output_dir = os.path.join("data", "output", case_id)
    os.makedirs(case_output_dir, exist_ok=True)

    # -------------------------
    # STEP 1: Auditor
    # -------------------------
    logger.info("Starting STEP 1: Auditor Agent (Parsing Documents)...")
    try:
        structured_denial_output: StructuredDenial | None = run_auditor_agent(
            client=client, denial_path=denial_path, policy_path=policy_path
        )
    except Exception as e:
        logger.exception("Auditor Agent raised an exception: %s", e)
        structured_denial_output = None

    if not structured_denial_output:
        logger.error("Workflow Halted: Auditor Agent failed to produce structured data.")
        return

    logger.info("Auditor SUCCESS. Denial Code: %s", getattr(structured_denial_output, "denial_code", "N/A"))
    auditor_out_path = os.path.join(case_output_dir, "auditor_output.json")
    save_json_to_file(structured_denial_output, auditor_out_path)

    # -------------------------
    # STEP 2: Clinician
    # -------------------------
    logger.info("Starting STEP 2: Clinician Agent (Medical Evidence Search)...")
    try:
        clinical_evidence: EvidenceList | None = run_clinician_agent(client=client, denial_details=structured_denial_output)
    except Exception as e:
        logger.exception("Clinician Agent raised an exception: %s", e)
        clinical_evidence = None

    if not clinical_evidence or not getattr(clinical_evidence, "root", None):
        logger.warning("Clinician Agent returned no evidence; proceeding with empty EvidenceList.")
        clinical_evidence = EvidenceList(root=[])

    logger.info("Clinician SUCCESS. Articles found: %d", len(getattr(clinical_evidence, "root", [])))
    clinician_out_path = os.path.join(case_output_dir, "clinician_output.json")
    save_json_to_file(clinical_evidence, clinician_out_path)

    # -------------------------
    # STEP 3: Regulatory
    # -------------------------
    logger.info("Starting STEP 3: Regulatory Agent (Compliance Analysis)...")
    try:
        regulatory_result = run_regulatory_agent(structured_denial_output, session_dir=case_output_dir)
    except Exception as e:
        logger.exception("Regulatory Agent raised an exception: %s", e)
        regulatory_result = {}

    if not regulatory_result or regulatory_result.get("violation") == "SYSTEM_ERROR":
        logger.warning("Regulatory Agent failed or returned system error. Continuing without legal points.")
        regulatory_result = {}

    logger.info("Regulatory result: compliant=%s", regulatory_result.get("compliant", "N/A"))
    regulatory_out_path = os.path.join(case_output_dir, "regulatory_output.json")
    save_json_to_file(regulatory_result, regulatory_out_path)

    # -------------------------
    # STEP 4: Barrister
    # -------------------------
    logger.info("Starting STEP 4: Barrister Agent (Appeal Drafting)...")
    try:
        final_appeal_text = run_barrister_agent(
            client=client,
            denial_details=structured_denial_output,
            clinical_evidence=clinical_evidence,
            regulatory_evidence=regulatory_result,
        )
    except Exception as e:
        logger.exception("Barrister Agent raised an exception: %s", e)
        final_appeal_text = None

    if not final_appeal_text:
        logger.error("Workflow Halted: Barrister Agent failed to generate appeal.")
        return

    logger.info("Barrister SUCCESS: Appeal drafted.")
    barrister_case_path = os.path.join(case_output_dir, "barrister_output.txt")
    save_json_to_file(final_appeal_text, barrister_case_path)

    # Backward-compatible top-level output
    try:
        denial_code_safe = getattr(structured_denial_output, "denial_code", "UNKNOWN").replace(" ", "_")
        output_filename = f"appeal_{case_id}_{denial_code_safe}.txt"
        output_path = os.path.join("data", "output", output_filename)
        save_json_to_file(final_appeal_text, output_path)
    except Exception:
        logger.exception("Failed to write top-level appeal file.")

    # -------------------------
    # STEP 5: Judge
    # -------------------------
    logger.info("Starting STEP 5: Judge Agent (Validation and Scoring)...")
    try:
        scorecard = run_judge_agent(case_output_dir)
        if scorecard:
            logger.info("Judge Agent SUCCESS. Final Status: %s, Score: %s", scorecard.status, scorecard.overall_score)
        else:
            logger.warning("Judge Agent returned no scorecard.")
    except Exception as e:
        logger.exception("Judge Agent raised an exception: %s", e)

    logger.info("✅ --- Advocai Workflow Complete ---")


if __name__ == "__main__":
    client = initialize_gemini_client()
    if not client:
        logger.critical("Client initialization failed. Exiting.")
        sys.exit(1)

    case_id = sys.argv[1] if len(sys.argv) > 1 else "case_1"
    DENIAL_PATH = os.path.join("data", "input", f"denial_{case_id}.pdf")
    POLICY_PATH = os.path.join("data", "input", f"policy_{case_id}.pdf")

    logger.info("Loading Test Case: %s...", case_id)
    if not os.path.exists(DENIAL_PATH) or not os.path.exists(POLICY_PATH):
        logger.critical("Input files not found for case ID: %s. Expected files:\n - %s\n - %s", case_id, DENIAL_PATH, POLICY_PATH)
        sys.exit(2)

    orchestrate_advocai_workflow(client, DENIAL_PATH, POLICY_PATH, case_id)
