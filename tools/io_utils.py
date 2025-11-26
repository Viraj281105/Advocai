# tools/io_utils.py
"""
Advocai – Universal JSON & Model IO Utilities
Safe saving, robust JSON extraction, Gemini/LLM cleanup,
and debugging helpers for all agents.
"""

import json
import re
import logging
import os
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel

logger = logging.getLogger("io_utils")


# ---------------------------------------------------------
# FILE-SAFE SAVE HELPERS
# ---------------------------------------------------------
def safe_save_model_json(
    model: BaseModel,
    path: str,
    *,
    ensure_ascii: bool = False,
    create_backup: bool = True
) -> None:
    """
    Save a Pydantic BaseModel to JSON safely.
    Handles pydantic v2 output, backup rotation, and crashes.
    """

    try:
        if create_backup and os.path.exists(path):
            _rotate_backup(path)

        # Pydantic v2: model_dump returns a fully JSON-safe dict
        obj = model.model_dump()

        with open(path, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, ensure_ascii=ensure_ascii)

        return

    except Exception as e:
        logger.exception(f"[IO] Failed to save model JSON → {path}: {e}")

    # Fallback dump (debug only)
    try:
        with open(path + ".debug.txt", "w", encoding="utf-8") as fh:
            fh.write("MODEL_DUMP_FALLBACK =\n")
            fh.write(repr(model))
    except Exception:
        pass


def _rotate_backup(path: str):
    """Rename existing file → file.bak (simple rotation)."""
    bak = path + ".bak"
    try:
        if os.path.exists(path):
            if os.path.exists(bak):
                os.remove(bak)
            os.rename(path, bak)
            logger.info(f"[IO] Backup created → {bak}")
    except Exception as e:
        logger.warning(f"[IO] Failed to rotate backup for {path}: {e}")


# ---------------------------------------------------------
# RAW LLM RESPONSE UTILITIES
# ---------------------------------------------------------
def save_llm_raw_dump(text: str, path: str):
    """Write the full raw LLM response for debugging."""
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        logger.debug(f"[IO] Raw LLM dump saved → {path}")
    except Exception as e:
        logger.error(f"[IO] Failed to write LLM dump: {e}")


def clean_llm_text(text: str) -> str:
    """
    Remove markdown fences, stray <<< >>> tokens,
    Gemini analysis comments, and whitespace noise.
    """

    if not text:
        return ""

    text = text.strip()

    # Remove ```json fences and plain ```
    text = re.sub(r"```(?:json)?", "", text)
    text = text.replace("```", "")

    # Strip XML/HTML tags occasionally emitted by models
    text = re.sub(r"<\/?(analysis|assistant|assistant_raw)[^>]*>", "", text)

    # Remove leading non-JSON clutter before first { or [
    first = min(
        [idx for idx in [text.find("{"), text.find("[")] if idx != -1] or [0]
    )
    text = text[first:].strip()

    return text


# ---------------------------------------------------------
# JSON Extraction (Robust)
# ---------------------------------------------------------
def extract_first_json_object(text: str) -> Optional[Union[Dict[str, Any], list]]:
    """
    Extracts the first valid JSON object OR array from text.
    Handles:
        { ... }
        [ ... ]
        nested objects
        trailing commas
        junk before/after
    """

    if not text:
        return None

    text = clean_llm_text(text)

    # Try direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # Brace/Bracket matching for both {} and []
    candidates = []

    # OBJECT SEARCH
    obj = _extract_balanced(text, "{", "}")
    if obj:
        candidates.append(obj)

    # ARRAY SEARCH
    arr = _extract_balanced(text, "[", "]")
    if arr:
        candidates.append(arr)

    # Try each candidate
    for c in candidates:
        for cleaned in _cleanup_json_variants(c):
            try:
                return json.loads(cleaned)
            except Exception:
                continue

    return None


def _extract_balanced(text: str, open_char: str, close_char: str) -> Optional[str]:
    """Return first balanced block for given bracket type."""
    start = text.find(open_char)
    if start == -1:
        return None

    stack = []
    for i in range(start, len(text)):
        if text[i] == open_char:
            stack.append(open_char)
        elif text[i] == close_char:
            if stack:
                stack.pop()
                if not stack:
                    return text[start:i + 1]
    return None


def _cleanup_json_variants(candidate: str):
    """Yield multiple variants of JSON cleaned up for parsing."""
    variants = [candidate]

    # remove trailing commas before } or ]
    cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
    variants.append(cleaned)

    # remove invisible unicode chars
    cleaned2 = cleaned.replace("\u200b", "")
    variants.append(cleaned2)

    # strip trailing junk
    last = max(candidate.rfind("}"), candidate.rfind("]"))
    if last != -1:
        variants.append(candidate[: last + 1])

    return variants


# ---------------------------------------------------------
# Convenience loader
# ---------------------------------------------------------
def load_json_file(path: str) -> Optional[Union[Dict[str, Any], list]]:
    """Safe JSON loader."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as e:
        logger.error(f"[IO] Failed loading JSON → {path}: {e}")
        return None
