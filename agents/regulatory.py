# agents/regulatory.py (FULLY PATCHED & STABLE)

import os
import json
import logging
import subprocess
import re
from typing import Optional, Union, Dict, Any, List

from google import genai
from google.genai import types

# -------------------------------------------------------------------
# LOGGER
# -------------------------------------------------------------------
logger = logging.getLogger("RegulatoryAgent")
logger.setLevel(logging.INFO)


# -------------------------------------------------------------------
# PATHS
# -------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUTES_PATH = os.path.join(PROJECT_ROOT, "data", "knowledge", "statutes.md")


# -------------------------------------------------------------------
# SAFE LOAD STATUTES
# -------------------------------------------------------------------
def load_statutes() -> str:
    if not os.path.exists(STATUTES_PATH):
        logger.warning(f"Statutes file not found: {STATUTES_PATH}")
        return ""
    try:
        with open(STATUTES_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read statutes: {e}")
        return ""


# -------------------------------------------------------------------
# CLEAN JSON TEXT
# -------------------------------------------------------------------
def _clean_json_text(raw: str) -> str:
    if not raw:
        return ""

    s = raw.strip()

    # Remove fenced blocks
    s = re.sub(r"```(?:json)?", "", s)
    s = s.replace("```", "")

    # Extract between FIRST { and LAST }
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        s = s[start:end + 1]

    return s.strip()


# -------------------------------------------------------------------
# Gemini call with defensive extraction
# -------------------------------------------------------------------
def analyze_with_gemini(prompt: str, max_output_tokens=2048) -> Optional[str]:
    try:
        client = genai.Client()
        logger.info("Using Gemini model: gemini-2.5-flash")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=types.GenerateContentConfig(
                max_output_tokens=max_output_tokens,
                temperature=0.0,
            )
        )

        # Extract response text safely
        if hasattr(response, "text") and response.text:
            return response.text.strip()

        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content") and candidate.content:
                parts = []
                for c in candidate.content:
                    if hasattr(c, "text") and c.text:
                        parts.append(c.text)
                if parts:
                    return "\n".join(parts).strip()

        logger.warning("Gemini returned empty or filtered response.")
        return None

    except Exception as e:
        logger.error(f"Gemini API failed: {e}")
        return None


# -------------------------------------------------------------------
# OLLAMA fallback (encoding-safe)
# -------------------------------------------------------------------
def analyze_with_ollama(prompt: str) -> Optional[str]:
    env = os.environ.copy()
    env["LANG"] = "C.UTF-8"
    env["LC_ALL"] = "C.UTF-8"

    try:
        result = subprocess.run(
            ["ollama", "run", "llama3.1"],
            input=prompt,
            text=True,
            encoding="utf-8",
            errors="ignore",
            capture_output=True,
            env=env,
            check=True
        )
        return result.stdout.strip()
    except FileNotFoundError:
        logger.error("Ollama CLI not found.")
        return None
    except subprocess.CalledProcessError as c:
        logger.error(f"Ollama failed: {c.stderr}")
        return None
    except Exception as e:
        logger.error(f"Ollama unexpected error: {e}")
        return None


# -------------------------------------------------------------------
# BUILD PROMPT
# -------------------------------------------------------------------
def _build_prompt(statutes_text: str, denial: Any) -> str:

    # Convert Pydantic → dict safely
    if hasattr(denial, "model_dump"):
        ctx = denial.model_dump()
    elif isinstance(denial, dict):
        ctx = denial
    else:
        ctx = {
            "denial_code": getattr(denial, "denial_code", ""),
            "insurer_reason_snippet": getattr(denial, "insurer_reason_snippet", ""),
            "policy_clause_text": getattr(denial, "policy_clause_text", ""),
            "procedure_denied": getattr(denial, "procedure_denied", "")
        }

    ctx.pop("raw_evidence_chunks", None)

    denial_json = json.dumps(ctx, indent=2)

    return f"""
You are an Indian Health Insurance Legal Expert (IRDAI + CPA + Ombudsman Rules).

Your goal: analyze this insurance denial for compliance.

Return STRICT JSON ONLY — NO extra text, NO markdown, NO comments.

Statutes:
{statutes_text}

Structured Denial Context:
{denial_json}

Required JSON format:
{{
  "compliant": true/false,
  "violation": "<short string>",
  "argument": "<max 150 words legal reasoning>",
  "action": "<reverse denial | manual review | request info>",
  "legal_points": [
    {{
      "statute": "<name>",
      "summary": "<2–3 sentence explanation>",
      "relevance_score": <0.0-1.0>
    }}
  ]
}}
"""


# -------------------------------------------------------------------
# MAIN REGULATORY PIPELINE
# -------------------------------------------------------------------
def run_regulatory_agent(
    structured_denial,
    session_dir="data/output/",
    save_filename="regulatory_output.json",
    use_gemini=True,
) -> Dict[str, Any]:

    os.makedirs(session_dir, exist_ok=True)

    statutes = load_statutes()
    prompt = _build_prompt(statutes, structured_denial)

    logger.info("Running regulatory analysis...")

    raw = analyze_with_gemini(prompt) if use_gemini else None
    if not raw:
        logger.warning("Gemini failed; falling back to Ollama.")
        raw = analyze_with_ollama(prompt)

    if not raw:
        logger.error("Both models failed. Using manual_review fallback.")
        fallback = {
            "compliant": False,
            "violation": "SYSTEM_ERROR",
            "argument": "LLMs failed to generate analysis.",
            "action": "manual_review_required",
            "legal_points": []
        }
        _save_json(session_dir, save_filename, fallback)
        return fallback

    # ---------------- PARSE JSON ----------------
    cleaned = _clean_json_text(raw)

    try:
        parsed = json.loads(cleaned)
    except Exception:
        # Try extracting JSON via regex
        json_match = re.search(r"\{[\s\S]*\}", cleaned)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
            except:
                parsed = None
        else:
            parsed = None

    if parsed is None:
        logger.error("LLM output unparsable. Using fallback structure.")
        parsed = {
            "compliant": False,
            "violation": "UNPARSABLE_JSON",
            "argument": raw[:250],
            "action": "manual_review_required",
            "legal_points": []
        }

    # Normalize types:
    result = {
        "compliant": bool(parsed.get("compliant")),
        "violation": str(parsed.get("violation", "")),
        "argument": str(parsed.get("argument", "")),
        "action": str(parsed.get("action", "")),
        "legal_points": []
    }

    # Normalize LP
    lp = parsed.get("legal_points", [])
    if isinstance(lp, list):
        for item in lp:
            if not isinstance(item, dict):
                continue
            statute = str(item.get("statute", item.get("reference", "unknown")))
            summary = str(item.get("summary", item.get("explanation", "")))
            try:
                score = float(item.get("relevance_score", 0))
            except:
                score = 0.0
            result["legal_points"].append({
                "statute": statute,
                "summary": summary,
                "relevance_score": max(0.0, min(1.0, score))
            })

    _save_json(session_dir, save_filename, result)
    return result


# -------------------------------------------------------------------
# SAVE JSON HELPER
# -------------------------------------------------------------------
def _save_json(folder, filename, obj):
    path = os.path.join(folder, filename)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2)
        logger.info(f"Regulatory output saved → {path}")
    except Exception as e:
        logger.error(f"Failed to save regulatory output: {e}")
