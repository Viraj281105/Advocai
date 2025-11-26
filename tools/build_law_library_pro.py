#!/usr/bin/env python3
"""
Advocai – Law Library Builder (Ultra-Stable Edition)
Safe downloads, correct metadata handling, reproducible knowledge index.
"""

import os
import time
import json
import hashlib
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import re

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("LawLibraryBuilder")

# ----------------------------------------------------------
# OPTIONAL PDF Metadata
# ----------------------------------------------------------
try:
    from pypdf import PdfReader
    _HAS_PDF = True
    logger.info("pypdf available for metadata extraction.")
except Exception:
    _HAS_PDF = False
    logger.warning("pypdf missing. Install: pip install pypdf")

# ----------------------------------------------------------
# CONFIG (centralized for stability)
# ----------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
KNOWLEDGE_DIR = os.path.join(DATA_DIR, "knowledge")
POLICY_DIR = os.path.join(KNOWLEDGE_DIR, "policies")

STATUTES_PATH = os.path.join(KNOWLEDGE_DIR, "statutes.md")
INDEX_PATH = os.path.join(KNOWLEDGE_DIR, "knowledge_index.json")
README_PATH = os.path.join(KNOWLEDGE_DIR, "README.md")

DOWNLOAD_TIMEOUT = (5, 30)     # connect/read
CHUNK_SIZE = 8192
MIN_VALID_PDF_SIZE = 2 * 1024  # 2 KB minimum safe size
SLEEP_BETWEEN_DOWNLOADS = 1.0

# ----------------------------------------------------------
# STATUTES CONTENT (immovable base)
# ----------------------------------------------------------
STATUTES_CONTENT = """# INDIAN LEGAL KNOWLEDGE BASE (IRDAI, CPA & OMBUDSMAN)

## 1. CLAIM SETTLEMENT & INTEREST (The "30 Day" Rule)
IRDAI Regulations (2017) Reg 15(10):
- Insurer must settle or reject a claim within 30 days.
- Investigation: 45 days max.
- Penalty interest: 2% above Bank Rate.

## 2. MORATORIUM (5 Year Rule)
IRDAI Master Circular 2024:
- After 60 months of continuous cover, claim cannot be rejected for non-disclosure unless fraud is proven.

## 3. CONSUMER PROTECTION ACT 2019
Wrongful repudiation = Deficiency in Service.

## 4. INSURANCE OMBUDSMAN RULES 2017
- Handles disputes, repudiations.
- Cap: ₹30 Lakh.
- Free & binding on insurer.

## 5. AMBIGUITY INTERPRETATION (Contra Proferentem)
IRDAI Plain Language Circular (2018):
- Ambiguities (“experimental”, “unproven”) must favor the policyholder.

## 6. EXCLUSIONS – STANDARDIZED
- Exclusions must be clear.
- Experimental treatment exclusions cannot override necessity without evidence.
"""

# ----------------------------------------------------------
# UTILITIES
# ----------------------------------------------------------
def setup_directories():
    os.makedirs(POLICY_DIR, exist_ok=True)
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
    logger.info(f"[INIT] Directories ready: {KNOWLEDGE_DIR}")

def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return "ERROR"

def safe_filename(name: str) -> str:
    return re.sub(r"[/:\\]", "_", name)

def download_file(url: str, dst_path: str) -> bool:
    if os.path.exists(dst_path) and os.path.getsize(dst_path) > MIN_VALID_PDF_SIZE:
        logger.info(f"[SKIP] Exists: {os.path.basename(dst_path)}")
        return True

    headers = {"User-Agent": "AdvocaiBot/1.0"}

    try:
        with requests.get(url, headers=headers, stream=True, timeout=DOWNLOAD_TIMEOUT) as r:
            r.raise_for_status()

            tmp_path = dst_path + ".part"
            with open(tmp_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)

            os.replace(tmp_path, dst_path)
            logger.info(f"[OK] Downloaded: {os.path.basename(dst_path)}")
            return True

    except Exception as e:
        logger.error(f"[ERR] Download failed: {os.path.basename(dst_path)} → {e}")
        return False

def extract_pdf_metadata(path: str) -> Dict[str, Any]:
    if not _HAS_PDF or not os.path.exists(path):
        return {"title": None, "author": None, "pages": None}

    meta = {"title": None, "author": None, "pages": None}
    try:
        reader = PdfReader(path)
        info = reader.metadata or {}

        meta["title"] = info.get("/Title")
        meta["author"] = info.get("/Author")

        try:
            meta["pages"] = len(reader.pages)
        except Exception:
            meta["pages"] = None

    except Exception as e:
        logger.warning(f"[WARN] PDF metadata error ({os.path.basename(path)}): {e}")

    return meta

def infer_insurer_from_filename(filename: str) -> Optional[str]:
    mapping = {
        r"\bstar\b": "STAR HEALTH",
        r"\bhdfc\b": "HDFC ERGO",
        r"\bergo\b": "HDFC ERGO",
        r"\bniva\b|\bbupa\b": "NIVA BUPA",
        r"\bicici\b": "ICICI LOMBARD",
        r"\baditya\b": "ADITYA BIRLA",
        r"\bsbi\b": "SBI GENERAL",
        r"\btata\b": "TATA AIG",
    }
    low = filename.lower()
    for pattern, insurer in mapping.items():
        if re.search(pattern, low):
            return insurer
    return None

# ----------------------------------------------------------
# POLICY URLS
# ----------------------------------------------------------
POLICY_URLS = {
    "Star_Comprehensive_Policy_2024.pdf": "https://irdai.gov.in/documents/37343/931203/SHAHLIP22028V072122_HEALTH2050.pdf/70aade12-d528-1155-a8b7-c03d2cfecd15?version=1.1&download=true",
    "HDFC_ERGO_Optima_Restore.pdf": "https://algatesinsurance.in/resources/policy-documents/hdfc-ergo/optima-restore-policy-wordings.pdf",
    "Niva_Bupa_ReAssure_2.0.pdf": "https://transactions.nivabupa.com/pages/doc/policy_wording/ReAssure-2.0-Policy-Wording.pdf",
    "ICICI_Lombard_iHealth.pdf": "https://www.icicilombard.com/docs/default-source/policy-wordings-product-brochure/complete-health-insurance-(ihealth)-new.pdf",
    "Aditya_Birla_Activ_Health.pdf": "https://www.adityabirlacapital.com/healthinsurance/assets/pdf/policy-wording-form.pdf",
    "SBI_General_Arogya_Sanjeevani.pdf": "https://content.sbigeneral.in/uploads/e14cc6abce7d4f4a8e9d0f1cf6f212e8.pdf",
    "Tata_AIG_Medicare.pdf": "https://irdai.gov.in/documents/37343/931203/TATHLIP21225V022021_2020-2021.pdf/63626023-5d4a-32f7-2f30-0d58882c191c?version=1.1&download=true",
}

# ----------------------------------------------------------
# BUILD KNOWLEDGE INDEX
# ----------------------------------------------------------
def build_knowledge_index(policy_urls: Dict[str, str]) -> Dict[str, Any]:
    index: Dict[str, Any] = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "policies": [],
        "statutes": {"path": os.path.relpath(STATUTES_PATH, PROJECT_ROOT), "sha256": None},
    }

    # Write statutes ONCE here (removed duplication)
    with open(STATUTES_PATH, "w", encoding="utf-8") as f:
        f.write(STATUTES_CONTENT)

    index["statutes"]["sha256"] = sha256_of_file(STATUTES_PATH)

    for fname, url in policy_urls.items():
        safe = safe_filename(fname)
        dst = os.path.join(POLICY_DIR, safe)

        logger.info(f"[PROCESS] {safe}")

        if not download_file(url, dst):
            logger.warning(f"[SKIP] Download failed → {safe}")
            continue

        meta = extract_pdf_metadata(dst)
        checksum = sha256_of_file(dst)
        insurer = infer_insurer_from_filename(safe) or (meta.get("title") or "") or safe.split("_")[0]

        index["policies"].append({
            "filename": safe,
            "path": os.path.relpath(dst, PROJECT_ROOT),
            "url": url,
            "insurer": insurer,
            "title": meta.get("title"),
            "author": meta.get("author"),
            "pages": meta.get("pages"),
            "sha256": checksum,
            "downloaded_at": datetime.utcnow().isoformat() + "Z",
        })

        time.sleep(SLEEP_BETWEEN_DOWNLOADS)

    index["policies"].sort(key=lambda x: (x.get("insurer") or "", x["filename"]))

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    _write_readme(index)
    return index

def _write_readme(index: Dict[str, Any]):
    try:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(f"# Advocai Knowledge Index\nGenerated: {index['generated_at']}\n\n")
            f.write(f"## Policies ({len(index['policies'])})\n\n")
            for p in index["policies"]:
                f.write(f"- **{p['filename']}** (Insurer: {p['insurer']}) — Pages: {p.get('pages') or 'N/A'}, SHA256: {p['sha256']}\n")
            f.write("\n## Statutes\n")
            f.write(f"- `statutes.md` — SHA256: {index['statutes']['sha256']}\n")
    except Exception as e:
        logger.error(f"[ERR] Failed writing README: {e}")

# ----------------------------------------------------------
# MAIN ENTRY
# ----------------------------------------------------------
def build_law_library_pro():
    print("\n--- Building Advocai Legal Knowledge Base (PRO) ---\n")
    setup_directories()
    idx = build_knowledge_index(POLICY_URLS)

    print("\n🎉 Knowledge library ready.\n")
    print(f" - Statutes: {STATUTES_PATH}")
    print(f" - Policies: {POLICY_DIR}")
    print(f" - Index: {INDEX_PATH}")
    print(f" - PDF metadata: {_HAS_PDF}\n")

    return idx

if __name__ == "__main__":
    build_law_library_pro()
