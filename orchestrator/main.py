# orchestrator/main.py — Phase II Orchestrator (Checkpointing + Resume + Postgres, Final Stabilized)

import os
import sys
import json
import logging
from typing import Any, Union
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

# Agents
from agents.auditor import run_auditor_agent, StructuredDenial
from agents.clinician import run_clinician_agent, EvidenceList
from agents.regulatory import run_regulatory_agent
from agents.barrister import run_barrister_agent
from agents.judge import run_judge_agent

# Session Manager
from storage.session_manager import SessionManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - Orchestrator - %(levelname)s - %(message)s")
logger = logging.getLogger("AdvocaiOrchestrator")


# -------------------------------------------------------------
# Gemini client init
# -------------------------------------------------------------
def initialize_gemini_client() -> genai.Client | None:
    load_dotenv()
    try:
        client = genai.Client()
        logger.info("genai.Client initialized.")
        return client
    except Exception as e:
        logger.fatal(f"Could not initialize genai client: {e}")
        return None


# -------------------------------------------------------------
# Robust JSON/text saving utility
# -------------------------------------------------------------
def save_json_to_file(obj: Any, path: str) -> bool:
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        # BaseModel → dict
        if isinstance(obj, BaseModel):
            obj = obj.model_dump()

        # dict or list → JSON file
        if isinstance(obj, (dict, list)):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(obj, f, indent=2, ensure_ascii=False)
            return True

        # string → could be JSON or raw text
        if isinstance(obj, str):
            try:
                parsed = json.loads(obj)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(parsed, f, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(obj)
            return True

        # Fallback: attempt to jsonify
        with open(path, "w", encoding="utf-8") as f:
            json.dump(str(obj), f, indent=2, ensure_ascii=False)
        return True

    except Exception as e:
        logger.error(f"Failed to save file {path}: {e}")
        return False


# -------------------------------------------------------------
# Safe execution wrapper for checkpointed pipeline
# -------------------------------------------------------------
def safe_execute(stage: str, session_id: str, function, *args, **kwargs):
    """
    Wrapper that ensures:
    - checkpoint resume
    - saving JSON + raw text depending on output type
    - consistent logging
    """

    # Already executed? Load checkpoint.
    if SessionManager.should_skip_stage(session_id, stage):
        logger.info(f"[{stage.upper()}] Skipped — checkpoint already exists.")
        return SessionManager.load_checkpoint(session_id, stage)

    logger.info(f"[{stage.upper()}] Starting...")

    try:
        output = function(*args, **kwargs)

        if output is None or output == "":
            raise RuntimeError(f"{stage} returned no output.")

        # Determine checkpoint payloads
        if isinstance(output, dict):
            checkpoint_json = output
            raw_text = None
        elif isinstance(output, BaseModel):
            checkpoint_json = output.model_dump()
            raw_text = None
        elif isinstance(output, str):
            checkpoint_json = {}
            raw_text = output
        else:
            checkpoint_json = {"value": str(output)}
            raw_text = str(output)

        # Save checkpoint to Postgres
        SessionManager.save_checkpoint(
            session_id=session_id,
            stage=stage,
            output_json=checkpoint_json,
            raw_text=raw_text
        )

        logger.info(f"[{stage.upper()}] Success — checkpoint saved.")
        return output

    except Exception as e:
        logger.exception(f"[{stage.upper()}] FAILED.")
        SessionManager.mark_failure(session_id, stage, str(e), error_type=type(e).__name__)
        raise e


# -------------------------------------------------------------
# MAIN ORCHESTRATOR
# -------------------------------------------------------------
def orchestrate_advocai_workflow(client: genai.Client, denial_path: str, policy_path: str, case_id: str):

    logger.info("=== AdvocAI Phase II Workflow Initiated ===")

    logger.info("Initializing session...")
    session_id = SessionManager.start_new_session(metadata={"case_id": case_id})
    logger.info(f"Session ID: {session_id}")

    case_output_dir = os.path.join("data", "output", case_id)
    os.makedirs(case_output_dir, exist_ok=True)

    # ---------------------------------------------------------
    # STEP 1 — Auditor
    # ---------------------------------------------------------
    structured_denial: StructuredDenial = safe_execute(
        "auditor",
        session_id,
        run_auditor_agent,
        client=client,
        denial_path=denial_path,
        policy_path=policy_path
    )
    save_json_to_file(structured_denial, os.path.join(case_output_dir, "auditor_output.json"))

    # ---------------------------------------------------------
    # STEP 2 — Clinician
    # ---------------------------------------------------------
    clinical_evidence: EvidenceList = safe_execute(
        "clinician",
        session_id,
        run_clinician_agent,
        client=client,
        denial_details=structured_denial
    )
    save_json_to_file(clinical_evidence, os.path.join(case_output_dir, "clinician_output.json"))

    # ---------------------------------------------------------
    # STEP 3 — Regulatory
    # ---------------------------------------------------------
    regulatory_result = safe_execute(
        "regulatory",
        session_id,
        run_regulatory_agent,
        structured_denial_output=structured_denial,
        session_dir=case_output_dir
    )
    save_json_to_file(regulatory_result, os.path.join(case_output_dir, "regulatory_output.json"))

    # ---------------------------------------------------------
    # STEP 4 — Barrister
    # ---------------------------------------------------------
    final_appeal_text = safe_execute(
        "barrister",
        session_id,
        run_barrister_agent,
        client=client,
        denial_details=structured_denial,
        clinical_evidence=clinical_evidence,
        regulatory_evidence=regulatory_result
    )
    save_json_to_file(final_appeal_text, os.path.join(case_output_dir, "barrister_output.txt"))

    denial_code_safe = structured_denial.denial_code.replace(" ", "_")
    save_json_to_file(final_appeal_text, os.path.join("data", "output", f"appeal_{case_id}_{denial_code_safe}.txt"))

    # ---------------------------------------------------------
    # STEP 5 — Judge
    # ---------------------------------------------------------
    scorecard = safe_execute(
        "judge",
        session_id,
        run_judge_agent,
        session_dir=case_output_dir
    )
    save_json_to_file(scorecard.model_dump(), os.path.join(case_output_dir, "judge_scorecard.json"))

    logger.info("=== AdvocAI Phase II Workflow Complete ===")


# -------------------------------------------------------------
# CLI Entrypoint
# -------------------------------------------------------------
if __name__ == "__main__":
    client = initialize_gemini_client()
    if not client:
        logger.critical("Gemini client init failed. Exiting.")
        sys.exit(1)

    case_id = sys.argv[1] if len(sys.argv) > 1 else "case_1"
    denial_path = os.path.join("data", "input", f"denial_{case_id}.pdf")
    policy_path = os.path.join("data", "input", f"policy_{case_id}.pdf")

    if not os.path.exists(denial_path) or not os.path.exists(policy_path):
        logger.error(f"Missing input files for case_id={case_id}")
        sys.exit(2)

    orchestrate_advocai_workflow(client, denial_path, policy_path, case_id)
