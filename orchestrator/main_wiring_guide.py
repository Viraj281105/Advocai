"""
orchestrator/main.py  —  How to wire the emit callback
=====================================================

Your existing run_pipeline function needs ONE change:
accept an `emit` callback parameter and call it at each stage.

Below is the pattern to follow. Adapt it to your actual code.
"""

import time
from typing import Callable

# ── Your existing agent imports ────────────────────────────────────────────
from agents.auditor import AuditorAgent
from agents.clinician import ClinicianAgent
from agents.regulatory import RegulatoryAgent
from agents.barrister import BarristerAgent
from agents.judge import JudgeAgent


def run_pipeline(
    denial_path: str,
    policy_path: str,
    case_id: str,
    emit: Callable[[dict], None] = lambda e: None,   # <-- ADD THIS PARAM
) -> dict:
    """
    Run the 5-agent pipeline.
    emit() is called before and after each agent so the SSE
    endpoint can stream progress to the frontend in real time.

    emit event shape:
    {
        "type":    "agent_start" | "agent_done" | "agent_error",
        "agent":   "auditor" | "clinician" | "regulatory" | "barrister" | "judge",
        "elapsed_ms": int,          # only on agent_done
        "output":  { ... }          # only on agent_done — key snippet for UI
    }
    """

    results = {}

    # ── Helper ──────────────────────────────────────────────────────────
    def run_agent(name: str, fn: Callable) -> dict:
        emit({"type": "agent_start", "agent": name})
        t0 = time.time()
        try:
            output = fn()
            elapsed = int((time.time() - t0) * 1000)
            emit({
                "type": "agent_done",
                "agent": name,
                "elapsed_ms": elapsed,
                "output": _snippet(name, output),
            })
            return output
        except Exception as e:
            emit({"type": "agent_error", "agent": name, "message": str(e)})
            raise

    # ── Stage 1: Auditor ────────────────────────────────────────────────
    auditor = AuditorAgent(denial_path=denial_path, policy_path=policy_path)
    results["auditor"] = run_agent("auditor", auditor.run)

    # ── Stage 2 & 3: Clinician + Regulatory (can run after auditor) ─────
    clinician = ClinicianAgent(auditor_output=results["auditor"])
    results["clinician"] = run_agent("clinician", clinician.run)

    regulatory = RegulatoryAgent(auditor_output=results["auditor"])
    results["regulatory"] = run_agent("regulatory", regulatory.run)

    # ── Stage 4: Barrister ──────────────────────────────────────────────
    barrister = BarristerAgent(
        auditor_output=results["auditor"],
        clinician_output=results["clinician"],
        regulatory_output=results["regulatory"],
    )
    results["barrister"] = run_agent("barrister", barrister.run)

    # ── Stage 5: Judge ──────────────────────────────────────────────────
    judge = JudgeAgent(
        barrister_output=results["barrister"],
        clinician_output=results["clinician"],
        regulatory_output=results["regulatory"],
    )
    results["judge"] = run_agent("judge", judge.run)

    return results


def _snippet(agent: str, output: dict) -> dict:
    """
    Extract a small UI-safe snippet from each agent's full output.
    This is what appears on the agent card in the pipeline viewer.
    """
    try:
        if agent == "auditor":
            return {
                "procedure_denied": output.get("procedure_denied", ""),
                "denial_code": output.get("denial_code", ""),
            }
        if agent == "clinician":
            articles = output.get("root", output.get("articles", []))
            return {"article_count": len(articles)}
        if agent == "regulatory":
            points = output.get("legal_points", [])
            return {
                "statute_count": len(points),
                "top_statute": points[0].get("statute", "") if points else "",
            }
        if agent == "barrister":
            letter = output.get("letter", output.get("appeal_letter", ""))
            return {"preview": letter[:120] + "..." if len(letter) > 120 else letter}
        if agent == "judge":
            return {
                "score": output.get("clinical_alignment", 0),
                "recommendation": output.get("recommendation", ""),
            }
    except Exception:
        pass
    return {}
