# tools/document_reader.py
"""
Advocai – Robust PDF Text Extraction Utility
Handles broken IRDAI PDFs, metadata inconsistencies, Unicode cleanup,
and produces stable segments for downstream LLM agents.
"""

from pypdf import PdfReader
from typing import List, Dict, Any
import re
import os
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# CLEANUP HELPERS
# ---------------------------------------------------------
def _normalize_unicode(text: str) -> str:
    """Fix common PDF ligatures and weird unicode artifacts."""
    if not text:
        return ""
    replacements = {
        "ﬁ": "fi",
        "ﬂ": "fl",
        "ﬃ": "ffi",
        "ﬄ": "ffl",
        "–": "-",  # en dash
        "—": "-",  # em dash
        "\u00a0": " ",  # non-breaking space
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def clean_text_segment(text: str) -> str:
    """Normalize whitespace, join hyphenation, remove garbage."""
    if not text:
        return ""

    text = _normalize_unicode(text)

    # Join hyphenated words across line-breaks
    text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)

    # Replace newlines with spaces
    text = re.sub(r"[\r\n]+", " ", text)

    # Remove multiple spaces
    text = re.sub(r"\s{2,}", " ", text)

    return text.strip()


# ---------------------------------------------------------
# MAIN EXTRACTION FUNCTION
# ---------------------------------------------------------
def extract_text_from_document(file_path: str) -> Dict[str, Any]:
    """
    Extracts text & segments from PDF in a safe, fault-tolerant way.
    Returns dict with:
     - full_text_content
     - segments
     - metadata
     - page_count
     - success/error
    """

    if not os.path.exists(file_path):
        return {
            "error": f"File not found: {file_path}",
            "success": False,
            "full_text_content": "",
            "segments": [],
            "page_count": 0,
        }

    try:
        reader = PdfReader(file_path)
    except Exception as e:
        logger.error(f"[PDF ERROR] Cannot open {file_path}: {e}")
        return {
            "error": f"Failed to open PDF: {e}",
            "success": False,
            "full_text_content": "",
            "segments": [],
            "page_count": 0,
        }

    segments: List[str] = []
    full_text_buffer = []

    # ---------------------------------------------------------
    # Page-by-page extraction
    # ---------------------------------------------------------
    for i, page in enumerate(reader.pages):
        try:
            raw = page.extract_text()
        except Exception as e:
            logger.warning(f"[PDF Warning] Page {i+1} failed extraction: {e}")
            raw = ""

        raw = raw or ""  # ensure string

        # Normalize
        cleaned = clean_text_segment(raw)

        full_text_buffer.append(f"\n\n--- PAGE {i+1} ---\n\n{cleaned}")

        # --- Segment extraction ---
        # Paragraph detection: two or more newlines OR bullet/number patterns
        para_candidates = re.split(
            r"(?:\n\s*\n|•|\u2022|\n\d+\.)", raw, flags=re.MULTILINE
        )

        for seg in para_candidates:
            seg = clean_text_segment(seg)
            if not seg:
                continue
            # Lower threshold improves policy clause capture
            if len(seg) > 40:
                segments.append(seg)

    # Limit to 60 segments to avoid overfeeding LLM
    segments = segments[:60]

    # ---------------------------------------------------------
    # Metadata cleanup (PDF metadata keys are PDF objects)
    # ---------------------------------------------------------
    metadata = {}
    try:
        raw_meta = reader.metadata or {}
        for k, v in raw_meta.items():
            metadata[str(k)] = str(v) if v is not None else None
    except Exception:
        metadata = {}

    return {
        "source_file": file_path,
        "metadata": metadata,
        "full_text_content": "\n".join(full_text_buffer).strip(),
        "segments": segments,
        "page_count": len(reader.pages),
        "success": True,
    }


# ---------------------------------------------------------
# Standalone test
# ---------------------------------------------------------
if __name__ == "__main__":
    import json

    path = input("PDF path: ").strip()
    out = extract_text_from_document(path)
    print(json.dumps(out, indent=2))
