# orchestrator/app.py — Phase II AdvocAI API Server (FIXED + ASYNC-SAFE)

import os
import uuid
import asyncio
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from storage.session_manager import SessionManager
from orchestrator.main import orchestrate_advocai_workflow, initialize_gemini_client

logger = logging.getLogger("AdvocaiAPI")
app = FastAPI(title="AdvocAI Orchestrator API", version="2.0")

# Initialize Gemini once
client = initialize_gemini_client()


# ================================================================
# Utility: Run sync orchestrator in thread executor
# ================================================================
def run_workflow_in_background(client, denial_path, policy_path, case_id):
    loop = asyncio.get_event_loop()
    # Run CPU/network-heavy orchestrator in a background thread
    loop.run_in_executor(
        None,
        orchestrate_advocai_workflow,
        client,
        denial_path,
        policy_path,
        case_id
    )


# ================================================================
# 1. START NEW WORKFLOW
# ================================================================
@app.post("/start")
async def start_workflow(
    denial: UploadFile = File(...),
    policy: UploadFile = File(...)
):
    """
    Start a new AdvocAI workflow.
    Accepts denial.pdf and policy.pdf.
    """

    # Create session
    session_id = SessionManager.start_new_session()
    case_id = f"case_{session_id}"

    case_input_dir = f"data/input/{case_id}"
    os.makedirs(case_input_dir, exist_ok=True)

    denial_path = f"{case_input_dir}/denial.pdf"
    policy_path = f"{case_input_dir}/policy.pdf"

    # Save uploaded PDFs
    try:
        with open(denial_path, "wb") as f:
            f.write(await denial.read())

        with open(policy_path, "wb") as f:
            f.write(await policy.read())
    except Exception as e:
        raise HTTPException(500, f"Failed to save uploaded files: {e}")

    # Launch workflow in background thread
    run_workflow_in_background(client, denial_path, policy_path, case_id)

    return {
        "session_id": session_id,
        "case_id": case_id,
        "status": "PROCESSING",
    }


# ================================================================
# 2. STATUS
# ================================================================
@app.get("/status/{session_id}")
def get_status(session_id: str):
    stage = SessionManager.get_resume_stage(session_id)

    if stage is None:
        raise HTTPException(404, "Session not found")

    return {
        "session_id": session_id,
        "last_completed_stage": stage,
        "is_resumable": stage is not None
    }


# ================================================================
# 3. RESUME WORKFLOW
# ================================================================
@app.post("/resume/{session_id}")
async def resume_workflow(session_id: str):
    """
    Resume a previously crashed/stopped workflow.
    """

    last_stage = SessionManager.get_resume_stage(session_id)
    if last_stage is None:
        raise HTTPException(404, "Session not found or no checkpoints")

    case_id = f"case_{session_id}"
    denial_path = f"data/input/{case_id}/denial.pdf"
    policy_path = f"data/input/{case_id}/policy.pdf"

    if not os.path.exists(denial_path) or not os.path.exists(policy_path):
        raise HTTPException(400, "Missing denial.pdf or policy.pdf for this session")

    # Continue workflow from next stage
    run_workflow_in_background(client, denial_path, policy_path, case_id)

    return {
        "session_id": session_id,
        "resume_from_stage": last_stage,
        "status": "RESUMING"
    }


# ================================================================
# 4. GET RESULT FILES
# ================================================================
@app.get("/result/{session_id}")
def get_result(session_id: str):
    case_id = f"case_{session_id}"
    out_dir = f"data/output/{case_id}"

    if not os.path.exists(out_dir):
        raise HTTPException(404, "Results not generated yet.")

    return {
        "session_id": session_id,
        "files": os.listdir(out_dir)
    }
