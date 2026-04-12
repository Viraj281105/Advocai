"""
orchestrator/app.py
"""

import asyncio
import json
import os
import uuid

from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# TEMP DEBUG — remove after fixing
import sys
print(f"[DEBUG] .env path: {env_path}", file=sys.stderr)
print(f"[DEBUG] .env exists: {env_path.exists()}", file=sys.stderr)
print(f"[DEBUG] POSTGRES_PASSWORD = '{os.getenv('POSTGRES_PASSWORD')}'", file=sys.stderr)

from pathlib import Path
from typing import Annotated, AsyncGenerator

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

# Auth — relative imports since auth/ lives inside orchestrator/
from .auth import router as auth_router, ensure_users_table
from .auth.router import get_current_user
from .auth.db import UserRecord

# Main pipeline — relative, NOT orchestrator.main
from .main import orchestrate_advocai_workflow, initialize_gemini_client

from storage.session_manager import get_cases_for_user, delete_case_for_user

app = FastAPI(title="AdvocAI API", version="1.0.0")
app.include_router(auth_router)

@app.on_event("startup")
async def startup():
    ensure_users_table()

    
# ── CORS — allow the Next.js dev server ────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory session store (replace with DB for production) ───────────────
# Structure: { session_id: { "status": ..., "events": [...], "result": ... } }
SESSIONS: dict = {}


# ══════════════════════════════════════════════════════════════════════════
#  POST /api/submit  —  Accept PDFs + case details, kick off pipeline
# ══════════════════════════════════════════════════════════════════════════
@app.post("/api/submit")
async def submit_case(
    denial_pdf: UploadFile = File(...),
    policy_pdf: UploadFile = File(...),
    patient_name: str = Form(...),
    insurer_name: str = Form(...),
    procedure_denied: str = Form(...),
    denial_date: str = Form(""),
    notes: str = Form(""),
):
    session_id = f"case_{uuid.uuid4().hex[:12]}"

    # Save uploaded PDFs to a temp session folder
    session_dir = Path(f"sessions/{session_id}")
    session_dir.mkdir(parents=True, exist_ok=True)

    denial_path = session_dir / "denial.pdf"
    policy_path = session_dir / "policy.pdf"

    denial_path.write_bytes(await denial_pdf.read())
    policy_path.write_bytes(await policy_pdf.read())

    # Store session metadata
    SESSIONS[session_id] = {
        "status": "queued",
        "events": [],
        "result": None,
        "meta": {
            "patient_name": patient_name,
            "insurer_name": insurer_name,
            "procedure_denied": procedure_denied,
            "denial_date": denial_date,
            "notes": notes,
            "denial_path": str(denial_path),
            "policy_path": str(policy_path),
        },
    }

    # Start the pipeline in the background
    asyncio.create_task(_run_pipeline_task(session_id))

    return {"session_id": session_id, "status": "queued"}


# ── Add these two endpoints anywhere in app.py ────────────────────────────────
 
@app.get("/api/cases")
async def list_cases(current_user: Annotated[UserRecord, Depends(get_current_user)]):
    """Return all cases for the authenticated user, newest first."""
    cases = await get_cases_for_user(str(current_user.id))
    return {"cases": cases}
 
 
@app.delete("/api/case/{session_id}", status_code=204)
async def delete_case(
    session_id: str,
    current_user: Annotated[UserRecord, Depends(get_current_user)],
):
    """Delete a case — only the owning user may delete it."""
    ok = await delete_case_for_user(session_id, str(current_user.id))
    if not ok:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

# ══════════════════════════════════════════════════════════════════════════
#  Background task — runs the 5-agent pipeline, appends SSE events
# ══════════════════════════════════════════════════════════════════════════
async def _run_pipeline_task(session_id: str):
    session = SESSIONS[session_id]
    session["status"] = "running"

    def emit(event: dict):
        """Append an event to the session's event queue."""
        session["events"].append(event)

    try:
        meta = session["meta"]

        result = await asyncio.to_thread(
            orchestrate_advocai_workflow,
            client=initialize_gemini_client(),
            denial_path=meta["denial_path"],
            policy_path=meta["policy_path"],
            case_id=session_id,
            emit=emit,
        )

        session["result"] = result
        session["status"] = "done"

        # Compile PDF packet
        from tools.pdf_compiler import compile_appeal_packet
        try:
            compile_appeal_packet(
                case_dir=f"data/output/{session_id}",
                output_path=f"sessions/{session_id}/appeal_packet.pdf"
            )
        except Exception as pdf_err:
            logger.warning(f"PDF compile failed: {pdf_err}")

        emit({"type": "pipeline_done", "session_id": session_id})

    except Exception as e:
        session["status"] = "error"
        emit({"type": "error", "message": str(e)})

# ══════════════════════════════════════════════════════════════════════════
#  GET /api/case/{session_id}/stream  —  SSE endpoint
#  Frontend connects here with EventSource and receives live agent events
# ══════════════════════════════════════════════════════════════════════════
@app.get("/api/case/{session_id}/stream")
async def stream_case(session_id: str):
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator() -> AsyncGenerator[str, None]:
        session = SESSIONS[session_id]
        sent_index = 0          # track which events we've already sent
        max_wait = 120          # give up after 2 minutes of silence

        for _ in range(max_wait * 10):   # poll every 100ms
            events = session["events"]

            # Send any new events
            while sent_index < len(events):
                event = events[sent_index]
                sent_index += 1
                # SSE format: "data: {json}\n\n"
                yield f"data: {json.dumps(event)}\n\n"

            # Pipeline finished — send a final event and close
            if session["status"] in ("done", "error"):
                yield f"data: {json.dumps({'type': 'close'})}\n\n"
                return

            await asyncio.sleep(0.1)

        # Timeout
        yield f"data: {json.dumps({'type': 'timeout'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",        # disable nginx buffering
            "Connection": "keep-alive",
        },
    )


# ══════════════════════════════════════════════════════════════════════════
#  GET /api/case/{session_id}/status  —  Simple polling fallback
# ══════════════════════════════════════════════════════════════════════════
@app.get("/api/case/{session_id}/status")
async def get_status(session_id: str):
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    session = SESSIONS[session_id]
    return {
        "session_id": session_id,
        "status": session["status"],
        "events": session["events"],
    }


# ══════════════════════════════════════════════════════════════════════════
#  GET /api/case/{session_id}/result  —  Full pipeline output
# ══════════════════════════════════════════════════════════════════════════
@app.get("/api/case/{session_id}/result")
async def get_result(session_id: str):
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    session = SESSIONS[session_id]
    if session["status"] != "done":
        raise HTTPException(status_code=202, detail="Pipeline still running")
    return session["result"]


# ══════════════════════════════════════════════════════════════════════════
#  GET /api/case/{session_id}/download  —  Download compiled PDF packet
# ══════════════════════════════════════════════════════════════════════════
@app.get("/api/case/{session_id}/download")
async def download_packet(session_id: str):
    pdf_path = Path(f"sessions/{session_id}/appeal_packet.pdf")
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not yet generated")
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"appeal_{session_id}.pdf",
    )


# ══════════════════════════════════════════════════════════════════════════
#  Health check
# ══════════════════════════════════════════════════════════════════════════
@app.get("/health")
async def health():
    return {"status": "ok", "sessions": len(SESSIONS)}
