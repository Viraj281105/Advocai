import os
import logging
import time
from google import genai
from google.genai import types
import subprocess
import json

# ------------------------------------------------------
# CONFIG & PATHS (Auto-resolves correct directory)
# ------------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUTES_PATH = os.path.join(PROJECT_ROOT, "data", "knowledge", "statutes.md")

# ------------------------------------------------------
# LOGGING SETUP
# ------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - RegulatoryAgent - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RegulatoryAgent")

# ------------------------------------------------------
# READ STATUTES
# ------------------------------------------------------

def load_statutes():
    """Reads statutes.md safely."""
    if not os.path.exists(STATUTES_PATH):
        logger.warning(f"Statutes file not found at {STATUTES_PATH}. Using empty context.")
        return ""

    with open(STATUTES_PATH, "r", encoding="utf-8") as f:
        return f.read()

# ------------------------------------------------------
# GEMINI ANALYSIS
# ------------------------------------------------------

def analyze_with_gemini(prompt):
    """Attempts Gemini API, falls back safely."""
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        logger.info("Using Gemini model: gemini-1.5-flash")

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=256,
                temperature=0.1
            )
        )

        return response.text

    except Exception as e:
        logger.error(f"Gemini API Failed: {e}")
        return None

# ------------------------------------------------------
# LOCAL FALLBACK (OLLAMA — LLAMA 3.1)
# ------------------------------------------------------

def analyze_with_ollama(prompt):
    """Local fallback using Ollama (Llama 3.1)."""
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3.1"],
            input=prompt,
            text=True,
            capture_output=True,
        )
        return result.stdout.strip()

    except Exception as e:
        logger.error(f"Ollama fallback failed: {e}")
        return None

# ------------------------------------------------------
# MAIN AGENT ANALYSIS
# ------------------------------------------------------

def analyze_denial(denial_code):
    statutes = load_statutes()

    prompt = f"""
You are an Indian Health Insurance Regulatory Expert (IRDAI + CPA + Ombudsman Rules).

Here are the official statutes:

{statutes}

Now evaluate this denial reason:

DENIAL CODE: {denial_code}

Return output in JSON with fields:
- compliant (true/false)
- violation
- argument
- action
"""

    logger.info(f"Analyzing compliance for denial code: {denial_code}")

    # 1) Try Gemini
    result = analyze_with_gemini(prompt)

    if result:
        return result

    # 2) Fallback to Ollama (local Llama 3.1)
    logger.warning("Falling back to local Llama 3.1 (Ollama)...")
    result = analyze_with_ollama(prompt)

    if result:
        return result

    # 3) Final fail-safe
    return json.dumps({
        "compliant": True,
        "violation": "SYSTEM_ERROR",
        "argument": "Both Gemini and local LLM failed.",
        "action": "Manual review required."
    })

# ------------------------------------------------------
# TEST RUN
# ------------------------------------------------------

if __name__ == "__main__":
    print("\n--- 🕵️‍♂️ STARTING REGULATORY AGENT TEST ---\n")

    denial_code = "NON-DISCLOSURE"   # example
    output = analyze_denial(denial_code)

    print("\n--- 📄 AGENT REPORT ---")
    print(output)
