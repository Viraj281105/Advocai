"""
Advocai – PubMed Search Tool (Production-Ready Rewrite)
Clean, deterministic, LLM-safe, no stdout noise, consistent return type.
"""

import os
import re
import time
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
PUBMED_API_KEY = os.getenv("PUBMED_API_KEY")


# ----------------------------------------------------------------------
# SAFE XML EXTRACTION
# ----------------------------------------------------------------------
def _extract_text(node: ET.Element) -> str:
    """Recursively extract human-readable text from XML nodes."""
    if node is None:
        return ""

    parts = []
    if node.text:
        parts.append(node.text)

    for child in node:
        parts.append(_extract_text(child))
        if child.tail:
            parts.append(child.tail)

    combined = " ".join(parts)
    return re.sub(r"\s+", " ", combined).strip()


def _parse_pubmed_xml(xml_str: str) -> List[Dict[str, str]]:
    """Parse PubMed EFETCH XML into a structured list."""
    try:
        root = ET.fromstring(xml_str)
    except Exception:
        return []

    articles = []

    for article in root.findall(".//PubmedArticle"):
        pmid = (article.findtext(".//PMID") or "").strip()
        pmid = pmid if pmid else "N/A"

        title = article.findtext(".//ArticleTitle") or ""
        title = title.strip() if title else "No Title"

        abstract_parts = []
        for abs_el in article.findall(".//AbstractText"):
            txt = _extract_text(abs_el)
            if txt:
                abstract_parts.append(txt)

        abstract = " ".join(abstract_parts)
        abstract = re.sub(r"\s+", " ", abstract).strip()

        articles.append({
            "pubmed_id": pmid,
            "article_title": title,
            "abstract": abstract,
        })

    return articles


# ----------------------------------------------------------------------
# NETWORK LAYER (RETRY & TIMEOUT)
# ----------------------------------------------------------------------
def _safe_request(url: str, params: dict, retries: int = 3) -> Optional[requests.Response]:
    """Retry wrapper for network calls."""
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            return r
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(0.3)
    return None


# ----------------------------------------------------------------------
# MAIN API WRAPPER
# ----------------------------------------------------------------------
def pubmed_search(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Clean, LLM-safe PubMed API wrapper.
    ALWAYS returns a list of dicts.
    Never logs, never prints, never raises.
    """

    # Basic sanity check to avoid trash queries
    if not query or len(query.strip()) < 6:
        return []

    # --- STEP 1: ESEARCH ---
    esearch_params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results,
        "usehistory": "y",
        "api_key": PUBMED_API_KEY,
        "tool": "AdvocaiAgent",
    }

    r1 = _safe_request(f"{PUBMED_BASE_URL}esearch.fcgi", esearch_params)
    if not r1:
        return []

    try:
        data = r1.json()
    except Exception:
        return []

    ids = data.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []

    # --- STEP 2: EFETCH ---
    efetch_params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "xml",
        "api_key": PUBMED_API_KEY,
        "tool": "AdvocaiAgent",
    }

    r2 = _safe_request(f"{PUBMED_BASE_URL}efetch.fcgi", efetch_params)
    if not r2:
        return []

    return _parse_pubmed_xml(r2.text)


# ----------------------------------------------------------------------
# OPTIONAL LOCAL TESTING
# ----------------------------------------------------------------------
if __name__ == "__main__":
    test = pubmed_search("genomic sequencing clinical trial", max_results=2)
    print(test)
