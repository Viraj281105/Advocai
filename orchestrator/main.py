# orchestrator/main.py — Phase II Orchestrator (Ollama Local LLM)

import os
import sys
import json
import logging
import requests
from typing import Any, Union, Callable

from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

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
# Ollama client — drop-in replacement for genai.Client
# -------------------------------------------------------------
class OllamaClient:
    """
    Thin wrapper around Ollama's local REST API.
    Mimics the interface the agents expect so minimal
    changes are needed downstream.
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "mistral"):
        self.base_url = base_url
        self.model = model
        self._verify_connection()

    def _verify_connection(self):
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            r.raise_for_status()
            logger.info(f"Ollama connected at {self.base_url} — model: {self.model}")
        except Exception as e:
            logger.fatal(f"Cannot reach Ollama at {self.base_url}: {e}")
            logger.fatal("Make sure Ollama is running: ollama serve")
            raise RuntimeError(f"Ollama not reachable: {e}")

    def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.0,
        max_tokens: int = 2048,
        json_mode: bool = False,
        stream_callback: Callable[[str], None] = None,
    ) -> str:
        """
        Call Ollama /api/chat endpoint.
        Returns raw text string.
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if json_mode:
            payload["format"] = "json"

        if stream_callback:
            payload["stream"] = True

        try:
            if stream_callback:
                r = requests.post(f"{self.base_url}/api/chat", json=payload, stream=True, timeout=120)
                r.raise_for_status()
                full_text = []
                for line in r.iter_lines():
                    if line:
                        data = json.loads(line)
                        chunk = data.get("message", {}).get("content", "")
                        if chunk:
                            stream_callback(chunk)
                            full_text.append(chunk)
                return "".join(full_text).strip()
            else:
                r = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120)
                r.raise_for_status()
                return r.json().get("message", {}).get("content", "").strip()
        except Exception as e:
            logger.error(f"Ollama generate failed: {e}")
            return ""


def initialize_ollama_client() -> OllamaClient:
    """
    Initialize and return the Ollama client.
    Reads OLLAMA_BASE_URL and OLLAMA_MODEL from .env if set,
    otherwise uses sensible defaults.
    """
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "mistral")

    try:
        client = OllamaClient(base_url=base_url, model=model)
        return client
    except Exception as e:
        logger.fatal(f"Could not initialize Ollama client: {e}")
        return None


# Keep old name as alias so app.py import doesn't break yet
initialize_gemini_client = initialize_ollama_client


# -------------------------------------------------------------
# Robust JSON/text saving utility
# -------------------------------------------------------------
def save_json_to_file(obj: Any, path: str) -> bool:
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        if isinstance(obj, BaseModel):
            obj = obj.model_dump()

        if isinstance(obj, (dict, list)):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(obj, f, indent=2, ensure_ascii=False)
            return True

        if isinstance(obj, str):
            try:
                parsed = json.loads(obj)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(parsed, f, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(obj)
            return True

        with open(path, "w", encoding="utf-8") as f:
            json.dump(str(obj), f, indent=2, ensure_ascii=False)
        return True

    except Exception as e:
        logger.error(f"Failed to save file {path}: {e}")
        return False


# -------------------------------------------------------------
# Extract a small UI snippet from each agent's output
# -------------------------------------------------------------
def _extract_snippet(stage: str, output: Any) -> dict:
    try:
        if stage == "auditor":
            d = output.model_dump() if isinstance(output, BaseModel) else output
            return {
                "procedure_denied": d.get("procedure_denied", ""),
                "denial_code": d.get("denial_code", ""),
            }
        if stage == "clinician":
            d = output.model_dump() if isinstance(output, BaseModel) else output
            articles = d.get("root", d.get("articles", []))
            return {"article_count": len(articles)}
        if stage == "regulatory":
            d = output if isinstance(output, dict) else {}
            points = d.get("legal_points", [])
            return {
                "statute_count": len(points),
                "top_statute": points[0].get("statute", "") if points else "",
            }
        if stage == "barrister":
            text = output if isinstance(output, str) else str(output)
            return {"preview": text[:120] + "..." if len(text) > 120 else text}
        if stage == "judge":
            d = output.model_dump() if isinstance(output, BaseModel) else output
            return {
                "score": d.get("overall_score", 0),
                "status": d.get("status", ""),
            }
    except Exception:
        pass
    return {}


# -------------------------------------------------------------
# Safe execution wrapper
# -------------------------------------------------------------
def safe_execute(
    stage: str,
    session_id: str,
    function,
    *args,
    emit: Callable[[dict], None] = lambda e: None,
    force: bool = False,
    **kwargs
):
    import time

    if not force and SessionManager.should_skip_stage(session_id, stage):
        logger.info(f"[{stage.upper()}] Skipped — checkpoint exists.")
        output = SessionManager.load_checkpoint(session_id, stage)
        emit({"type": "agent_done", "agent": stage, "elapsed_ms": 0,
              "output": _extract_snippet(stage, output)})
        return output

    logger.info(f"[{stage.upper()}] Starting...")
    emit({"type": "agent_start", "agent": stage})
    t0 = time.time()

    try:
        output = function(*args, **kwargs)

        if output is None or output == "":
            raise RuntimeError(f"{stage} returned no output.")

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

        SessionManager.save_checkpoint(
            session_id=session_id,
            stage=stage,
            output_json=checkpoint_json,
            raw_text=raw_text,
        )

        elapsed = int((time.time() - t0) * 1000)
        emit({
            "type": "agent_done",
            "agent": stage,
            "elapsed_ms": elapsed,
            "output": _extract_snippet(stage, output),
        })

        logger.info(f"[{stage.upper()}] Success — checkpoint saved.")
        return output

    except Exception as e:
        logger.exception(f"[{stage.upper()}] FAILED.")
        emit({"type": "agent_error", "agent": stage, "message": str(e)})
        SessionManager.mark_failure(session_id, stage, str(e), error_type=type(e).__name__)
        raise e


# -------------------------------------------------------------
# MAIN ORCHESTRATOR
# -------------------------------------------------------------
def orchestrate_advocai_workflow(
    client: OllamaClient,
    denial_path: str,
    policy_path: str,
    case_id: str,
    emit: Callable[[dict], None] = lambda e: None,
):
    logger.info("=== AdvocAI Workflow Initiated (Local Ollama) ===")

    session_id = SessionManager.start_new_session(metadata={"case_id": case_id})
    logger.info(f"Session ID: {session_id}")

    case_output_dir = os.path.join("data", "output", case_id)
    os.makedirs(case_output_dir, exist_ok=True)

    # STEP 1 — Auditor
    structured_denial: StructuredDenial = safe_execute(
        "auditor", session_id,
        run_auditor_agent,
        client=client,
        denial_path=denial_path,
        policy_path=policy_path,
        emit=emit,
    )
    save_json_to_file(structured_denial, os.path.join(case_output_dir, "auditor_output.json"))

    # STEP 2 — Clinician
    clinical_evidence: EvidenceList = safe_execute(
        "clinician", session_id,
        run_clinician_agent,
        client=client,
        denial_details=structured_denial,
        emit=emit,
    )
    save_json_to_file(clinical_evidence, os.path.join(case_output_dir, "clinician_output.json"))

    # STEP 4 & 5 — Debate Loop
    max_debates = 2
    debates = 0
    final_appeal_text = None
    scorecard = None
    critique = None

    while True:
        final_appeal_text = safe_execute(
            "barrister", session_id,
            run_barrister_agent,
            client=client,
            denial_details=structured_denial,
            clinical_evidence=clinical_evidence,
            regulatory_evidence=regulatory_result,
            critique=critique,
            emit=emit,
            force=(debates > 0),
        )
        save_json_to_file(final_appeal_text, os.path.join(case_output_dir, "barrister_output.txt"))

        denial_code_safe = structured_denial.denial_code.replace(" ", "_")
        save_json_to_file(
            final_appeal_text,
            os.path.join("data", "output", f"appeal_{case_id}_{denial_code_safe}.txt")
        )

        scorecard = safe_execute(
            "judge", session_id,
            run_judge_agent,
            session_dir=case_output_dir,
            emit=emit,
            force=(debates > 0),
        )
        
        scorecard_dump = scorecard.model_dump() if hasattr(scorecard, "model_dump") else scorecard
        save_json_to_file(
            scorecard_dump,
            os.path.join(case_output_dir, "judge_scorecard.json")
        )

        overall_score = scorecard_dump.get("overall_score", 0) if isinstance(scorecard_dump, dict) else 0
        if overall_score >= 80 or debates >= max_debates:
            break

        critique = scorecard_dump.get("recommendation", "Improve the letter.")
        logger.info(f"=== DEBATE TRIGGERED === Score: {overall_score}. Critique: {critique}")
        emit({"type": "agent_pending", "agent": "judge"})
        debates += 1
    )

    logger.info("=== AdvocAI Workflow Complete ===")

    return {
        "auditor": structured_denial.model_dump() if isinstance(structured_denial, BaseModel) else structured_denial,
        "clinician": clinical_evidence.model_dump() if isinstance(clinical_evidence, BaseModel) else clinical_evidence,
        "regulatory": regulatory_result,
        "barrister": final_appeal_text,
        "judge": scorecard.model_dump() if isinstance(scorecard, BaseModel) else scorecard,
    }


# -------------------------------------------------------------
# CLI Entrypoint
# -------------------------------------------------------------
if __name__ == "__main__":
    client = initialize_ollama_client()
    if not client:
        logger.critical("Ollama client init failed. Is ollama running?")
        sys.exit(1)

    case_id = sys.argv[1] if len(sys.argv) > 1 else "case_1"
    denial_path = os.path.join("data", "input", f"denial_{case_id}.pdf")
    policy_path = os.path.join("data", "input", f"policy_{case_id}.pdf")

    if not os.path.exists(denial_path) or not os.path.exists(policy_path):
        logger.error(f"Missing input files for case_id={case_id}")
        sys.exit(2)

    orchestrate_advocai_workflow(client, denial_path, policy_path, case_id)