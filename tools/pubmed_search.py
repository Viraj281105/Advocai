# tools/pubmed_search.py
"""
Advocai – PubMed Search Tool (LLM-Safe Version)
Structured output, no stdout pollution, robust XML parsing, retries,
and JSON-return contract for Gemini function-call mode.
"""

import os
import json
import re
import time
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
PUBMED_API_KEY = os.getenv("PUBMED_API_KEY")


# ----------------------------------------------------------------------
# SAFER XML PARSING
# ----------------------------------------------------------------------
def _extract_text_recursive(element: ET.Element) -> str:
    """Extracts the full text content of an XML element, including children."""
    parts = []

    if element.text:
        parts.append(element.text)

    for child in element:
        parts.append(_extract_text_recursive(child))
        if child.tail:
            parts.append(child.tail)

    joined = " ".join(parts)
    return re.sub(r"\s+", " ", joined).strip()


def _parse_efetch_xml(xml_content: str) -> List[Dict[str, str]]:
    """Parse PubMed XML into structured article dicts."""
    articles = []
    try:
        root = ET.fromstring(xml_content)

        for article_element in root.findall(".//PubmedArticle"):
            pmid = (article_element.findtext(".//PMID") or "").strip() or "N/A"
            title = (article_element.findtext(".//ArticleTitle") or "").strip() or "No Title"

            abstracts = []
            for abs_el in article_element.findall(".//AbstractText"):
                txt = _extract_text_recursive(abs_el)
                if txt:
                    abstracts.append(txt)

            abstract = " ".join(abstracts)
            abstract = re.sub(r"\s+", " ", abstract).strip()

            articles.append({
                "article_title": title,
                "abstract": abstract,
                "pubmed_id": pmid,
            })

    except Exception as e:
        return []

    return articles


# ----------------------------------------------------------------------
# NETWORK WITH RETRY
# ----------------------------------------------------------------------
def _request_with_retry(url: str, params: dict, *, retries: int = 3, delay: float = 0.4):
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            return r
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(delay)
    return None


# ----------------------------------------------------------------------
# MAIN TOOL FUNCTION (LLM-SAFE)
# ----------------------------------------------------------------------
def pubmed_search(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    LLM-Safe PubMed API wrapper.
    ALWAYS returns a real LIST (never a JSON string, never prints).
    """

    if not query or len(query.strip()) < 6:
        return []

    params_esearch = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results,
        "usehistory": "y",
        "tool": "AdvocaiAgent",
        "api_key": PUBMED_API_KEY,
    }

    # STEP 1 — Search
    r = _request_with_retry(f"{PUBMED_BASE_URL}esearch.fcgi", params_esearch)
    if not r:
        return []

    try:
        data = r.json()
    except Exception:
        return []

    ids = data.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []

    # STEP 2 — Fetch full abstracts
    params_efetch = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "xml",
        "tool": "AdvocaiAgent",
        "api_key": PUBMED_API_KEY,
    }

    r2 = _request_with_retry(f"{PUBMED_BASE_URL}efetch.fcgi", params_efetch)
    if not r2:
        return []

    return _parse_efetch_xml(r2.text)


# ----------------------------------------------------------------------
# Allow local CLI testing (optional)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    out = pubmed_search("asymptomatic carotid stenosis clinical trial effectiveness", max_results=2)
    print(json.dumps(out, indent=2))
