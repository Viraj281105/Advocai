# agents/regulatory.py — FINAL PATCHED VERSION FOR WINDOWS + HYBRID FALLBACK

import os
import json
import logging
import re
import subprocess
from typing import Any, Dict, Optional, List

from google import genai
from google.genai import types

logger = logging.getLogger("RegulatoryAgent")
logger.setLevel(logging.INFO)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUTES_PATH = os.path.join(PROJECT_ROOT, "data", "knowledge", "statutes.md")

MODEL_NAME = "gemini-2.5-flash"

# ---- FULL WINDOWS PATH TO OLLAMA ----
OLLAMA_EXE = r"C:\Users\VIRAJ\AppData\Local\Programs\Ollama\ollama.exe"

# ============================================================
# Helpers
# ============================================================
def load_statutes() -> str:
    try:
        if not os.path.exists(STATUTES_PATH):
            logger.warning(f"Statutes file missing: {STATUTES_PATH}")
            return ""
        with open(STATUTES_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read statutes: {e}")
        return ""


def _clean_json_payload(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    s = re.sub(r"```json|```", "", s)

    start = s.find("{")
    end = s.rfind("}")
    return s[start:end + 1] if start != -1 and end != -1 else s


def _extract_gemini_text(resp) -> Optional[str]:
    if hasattr(resp, "text") and resp.text:
        return resp.text.strip()

    try:
        parts = resp.candidates[0].content.parts
        texts = []
        for p in parts:
            if hasattr(p, "text") and p.text:
                texts.append(p.text)
        return "\n".join(texts).strip() if texts else None
    except Exception:
        return None


def _run_ollama(prompt: str) -> Optional[str]:
    """Windows-safe Ollama execution with timeout."""
    env = os.environ.copy()
    env["LANG"] = "C.UTF-8"
    env["LC_ALL"] = "C.UTF-8"

    try:
        result = subprocess.run(
            [OLLAMA_EXE, "run", "llama3.1"],
            input=prompt,
            text=True,
            encoding="utf-8",
            errors="ignore",
            capture_output=True,
            env=env,
            timeout=8  # <-- IMPORTANT: prevents workflow hang
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        logger.error("Ollama timed out after 8 seconds.")
        return None
    except FileNotFoundError:
        logger.error("Ollama binary not found at specified path.")
        return None
    except Exception as e:
        logger.error(f"Ollama failure: {e}")
        return None


def _save_json(folder: str, filename: str, obj: dict):
    try:
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2)
        logger.info(f"Regulatory output saved → {path}")
    except Exception as e:
        logger.error(f"Failed to save regulatory output: {e}")


# ============================================================
# Prompt Builder
# ============================================================
def _make_prompt(statutes: str, denial: Any) -> str:

    if hasattr(denial, "model_dump"):
        ctx = denial.model_dump()
    elif isinstance(denial, dict):
        ctx = denial
    else:
        ctx = {
            "denial_code": getattr(denial, "denial_code", ""),
            "insurer_reason_snippet": getattr(denial, "insurer_reason_snippet", ""),
            "policy_clause_text": getattr(denial, "policy_clause_text", ""),
            "procedure_denied": getattr(denial, "procedure_denied", ""),
        }

    ctx.pop("raw_evidence_chunks", None)

    return f"""
You are a senior Indian Health Insurance Legal Expert (IRDAI, CPA, Ombudsman Rules).

Task:
Analyze whether the insurer’s denial is compliant.

Return ONLY JSON. No markdown. No prose.

Statutes:
{statutes}

Structured Context:
{json.dumps(ctx, indent=2)}

Required JSON:
{{
  "compliant": true/false,
  "violation": "<short code>",
  "argument": "<short legal reasoning>",
  "action": "<reverse denial | manual review | request info>",
  "legal_points": [
    {{
      "statute": "<name>",
      "summary": "<short explanation>",
      "relevance_score": <0.0-1.0>
    }}
  ]
}}
"""


# ============================================================
# MAIN REGULATORY AGENT
# ============================================================
def run_regulatory_agent(
    structured_denial_output: Any,
    clinical_evidence: Any = None,
    session_dir: str = "data/output/",
    save_filename: str = "regulatory_output.json",
    use_gemini: bool = True,
) -> Dict[str, Any]:

    statutes = load_statutes()
    prompt = _make_prompt(statutes, structured_denial_output)

    logger.info("[Regulatory] Starting legal compliance analysis...")

    # -----------------------------------------------------
    # 1. Gemini primary
    # -----------------------------------------------------
    raw = None
    if use_gemini:
        try:
            client = genai.Client()
            resp = client.models.generate_content(
                model=MODEL_NAME,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=2048,
                    response_mime_type="application/json",
                )
            )
            raw = _extract_gemini_text(resp)
        except Exception as e:
            logger.error(f"[Regulatory] Gemini ERROR: {e}")
            raw = None

    # -----------------------------------------------------
    # 2. Ollama fallback
    # -----------------------------------------------------
    if not raw or raw.strip() == "":
        logger.warning("[Regulatory] Gemini returned empty/unsafe payload.")
        logger.warning("[Regulatory] Switching to Ollama...")
        raw = _run_ollama(prompt)

    # -----------------------------------------------------
    # 3. Final failsafe
    # -----------------------------------------------------
    if not raw:
        logger.error("[Regulatory] ALL LLMs failed → SYSTEM_ERROR fallback.")
        result = {
            "compliant": False,
            "violation": "SYSTEM_ERROR",
            "argument": "LLM processing failed.",
            "action": "manual_review_required",
            "legal_points": []
        }
        _save_json(session_dir, save_filename, result)
        return result

    # -----------------------------------------------------
    # 4. Parse JSON
    # -----------------------------------------------------
    cleaned = _clean_json_payload(raw)
    try:
        parsed = json.loads(cleaned)
    except Exception:
        logger.error("[Regulatory] JSON parsing failed.")
        parsed = {
            "compliant": False,
            "violation": "UNPARSABLE_JSON",
            "argument": raw[:200],
            "action": "manual_review_required",
            "legal_points": []
        }

    # -----------------------------------------------------
    # 5. Normalize output
    # -----------------------------------------------------
    result = {
        "compliant": bool(parsed.get("compliant")),
        "violation": str(parsed.get("violation", "")),
        "argument": str(parsed.get("argument", "")),
        "action": str(parsed.get("action", "")),
        "legal_points": []
    }

    lp = parsed.get("legal_points", [])
    if isinstance(lp, list):
        for item in lp:
            if isinstance(item, dict):
                result["legal_points"].append({
                    "statute": str(item.get("statute", "unknown")),
                    "summary": str(item.get("summary", "")),
                    "relevance_score": float(item.get("relevance_score", 0) or 0),
                })

    _save_json(session_dir, save_filename, result)
    return result
