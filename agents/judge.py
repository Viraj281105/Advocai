"""
Judge Agent — Enterprise-Stable Rewrite
Consistent with new Auditor, Clinician, Regulatory, Barrister layers.
Deterministic scoring, NIL-safe evidence linking, robust Pydantic models.
"""

from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Any, Optional
from datetime import datetime
import difflib
import logging
import os
import json
import re

logger = logging.getLogger("JudgeAgent")
logger.setLevel(logging.INFO)


# ============================================================
# Pydantic Models
# ============================================================
class Issue(BaseModel):
    id: str
    severity: str = Field(..., description='"low" | "medium" | "high"')
    location_in_letter: Optional[Dict[str, int]] = None
    description: str
    evidence_refs: Optional[List[str]] = None
    suggested_fix: Optional[str] = None


class SubScores(BaseModel):
    factual_accuracy: int = Field(..., ge=0, le=100)
    citation_consistency: int = Field(..., ge=0, le=100)
    logical_adequacy: int = Field(..., ge=0, le=100)
    tone_professionalism: int = Field(..., ge=0, le=100)
    hallucination_risk: int = Field(..., ge=0, le=100)


class JudgeScorecard(BaseModel):
    overall_score: int
    status: str
    sub_scores: SubScores
    issues: List[Issue]
    confidence_estimate: float = Field(..., ge=0.0, le=1.0)
    meta: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    def compute_overall(cls, values):
        if "overall_score" in values:
            return values

        subs = values.get("sub_scores")
        if not subs:
            return values

        v = subs if isinstance(subs, dict) else subs.model_dump()

        overall = int(
            (
                v["factual_accuracy"]
                + v["citation_consistency"]
                + v["logical_adequacy"]
                + v["tone_professionalism"]
                - v["hallucination_risk"]
            ) / 5
        )

        values["overall_score"] = overall
        values["status"] = "approve" if overall >= 85 else "needs_revision"
        return values


# ============================================================
# Loaders
# ============================================================
def _load_json(path):
    if not os.path.exists(path):
        logger.warning(f"[Judge] Missing JSON at {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[Judge] JSON load failed: {e}")
        return None


def _load_text(path):
    if not os.path.exists(path):
        logger.warning(f"[Judge] Missing text at {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"[Judge] Failed to read: {e}")
        return None


def load_all_inputs(session_dir):
    return {
        "auditor": _load_json(os.path.join(session_dir, "auditor_output.json")),
        "clinician": _load_json(os.path.join(session_dir, "clinician_output.json")),
        "regulatory": _load_json(os.path.join(session_dir, "regulatory_output.json")),
        "barrister": _load_text(os.path.join(session_dir, "barrister_output.txt")),
    }


# ============================================================
# Text utilities
# ============================================================
def split_sentences(text: str) -> List[str]:
    if not text:
        return []
    text = re.sub(r"[\r\n]+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    return [p.strip() for p in parts if p.strip()]


def classify_sentences(sentences: List[str]) -> List[Dict[str, Any]]:
    claim_keywords = [
        "evidence", "clinical", "study", "trial", "research",
        "medically necessary", "medical necessity",
        "denial", "policy", "regulation", "coverage",
        "should be covered", "effective", "beneficial",
        "recommended", "indicated", "supports", "argue",
        "counter", "compliant", "unproven", "experimental",
    ]

    out = []
    for i, s in enumerate(sentences):
        lower = s.lower()
        is_claim = any(k in lower for k in claim_keywords)
        out.append({
            "sentence_index": i,
            "sentence": s,
            "label": "CLAIM" if is_claim else "NON_CLAIM"
        })
    return out


# ============================================================
# Evidence linking
# ============================================================
def link_evidence(sentence, auditor, clinician, regulatory):
    s = sentence.lower()
    matches = {"auditor": [], "clinician": [], "regulatory": []}

    # Auditor evidence
    if auditor:
        for chunk in auditor.get("raw_evidence_chunks", []):
            try:
                ratio = difflib.SequenceMatcher(None, s, chunk.lower()).ratio()
                if ratio > 0.35:
                    matches["auditor"].append(chunk[:60])
            except:
                pass

        dc = auditor.get("denial_code", "").lower()
        if dc and dc in s:
            matches["auditor"].append(f"DenialCode:{dc}")

        snippet = (auditor.get("insurer_reason_snippet") or "").lower()
        if snippet:
            core = snippet.split()[:4]
            if any(w in s for w in core):
                matches["auditor"].append("InsurerReasonSnippet")

    # Clinician evidence
    if clinician and isinstance(clinician, dict):
        for entry in clinician.get("root", []):
            combined = " ".join([
                (entry.get("article_title") or "").lower(),
                (entry.get("summary_of_finding") or "").lower(),
                str(entry.get("pubmed_id") or "").lower()
            ])

            ratio = difflib.SequenceMatcher(None, s, combined).ratio()
            pmid = str(entry.get("pubmed_id") or "").lower()
            if pmid and pmid in s:
                ratio = 1.0

            if ratio > 0.25:
                matches["clinician"].append(f"PMID:{pmid or 'unknown'}")

    # Regulatory evidence
    if regulatory and isinstance(regulatory, dict):
        lps = regulatory.get("legal_points", [])
        if isinstance(lps, list):
            for lp in lps:
                statute = (lp.get("statute") or lp.get("reference") or "").lower()
                summary = (lp.get("summary") or lp.get("argument") or "").lower()

                if statute in s:
                    matches["regulatory"].append(statute)
                else:
                    ratio = difflib.SequenceMatcher(None, s, summary).ratio()
                    if ratio > 0.22:
                        matches["regulatory"].append(statute or "reg_point")

    return matches


# ============================================================
# Scoring
# ============================================================
def score_claim(matches):
    score = 0
    if matches["auditor"]:
        score += 20
    if matches["clinician"]:
        score += 40
    if matches["regulatory"]:
        score += 40
    return score


def compute_subscores(claim_results):
    claims = [c for c in claim_results if c["label"] == "CLAIM"]
    if not claims:
        return SubScores(
            factual_accuracy=95,
            citation_consistency=95,
            logical_adequacy=95,
            tone_professionalism=90,
            hallucination_risk=0
        )

    supported = sum(1 for c in claims if c["score"] >= 30)
    halluc = sum(1 for c in claims if c["score"] == 0)

    factual = int((supported / len(claims)) * 100)
    halluc_risk = int((halluc / len(claims)) * 100)

    return SubScores(
        factual_accuracy=factual,
        citation_consistency=factual,
        logical_adequacy=factual,
        tone_professionalism=90,
        hallucination_risk=halluc_risk,
    )


# ============================================================
# Issue Detection
# ============================================================
def detect_issues(claim_results):
    issues = []
    counter = 1

    for c in claim_results:
        if c["label"] != "CLAIM":
            continue

        score = c["score"]
        idx = c["sentence_index"]

        if score == 0:
            issues.append(Issue(
                id=f"ISSUE-{counter}",
                severity="high",
                location_in_letter={"sentence_index": idx},
                description=f"Unsupported claim: '{c['sentence']}'",
                evidence_refs=[],
                suggested_fix="Add supporting clinical or regulatory evidence, or remove the claim."
            ))
            counter += 1
            continue

        missing = []
        if not c["matches"]["clinician"]:
            missing.append("clinical evidence")
        if not c["matches"]["regulatory"]:
            missing.append("regulatory evidence")

        if missing:
            refs = [x for src in c["matches"].values() for x in src]
            issues.append(Issue(
                id=f"ISSUE-{counter}",
                severity="medium",
                location_in_letter={"sentence_index": idx},
                description=f"Partially supported claim. Missing: {', '.join(missing)}",
                evidence_refs=list(set(refs)),
                suggested_fix="Strengthen argument by adding missing evidence."
            ))
            counter += 1

    return issues


# ============================================================
# Pipeline
# ============================================================
def run_judge_agent(session_dir="data/output/"):
    logger.info("[Judge] Loading agent outputs...")
    inp = load_all_inputs(session_dir)

    auditor = inp["auditor"]
    clinician = inp["clinician"]
    regulatory = inp["regulatory"]
    letter = inp["barrister"]

    if not letter:
        logger.error("[Judge] No barrister output found.")
        return None

    sentences = split_sentences(letter)
    labels = classify_sentences(sentences)

    claim_results = []
    for item in labels:
        s = item["sentence"]
        if item["label"] == "CLAIM":
            matches = link_evidence(s, auditor, clinician, regulatory)
            score = score_claim(matches)
        else:
            matches = {"auditor": [], "clinician": [], "regulatory": []}
            score = 0

        claim_results.append({
            **item,
            "matches": matches,
            "score": score
        })

    subs = compute_subscores(claim_results)
    issues = detect_issues(claim_results)

    scorecard = JudgeScorecard(
        sub_scores=subs,
        issues=issues,
        confidence_estimate=0.85,
        meta={"generated_at": datetime.utcnow().isoformat(), "version": "v2.0"}
    )

    # Save outputs
    os.makedirs(session_dir, exist_ok=True)

    json_path = os.path.join(session_dir, "judge_scorecard.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(scorecard.model_dump(), f, indent=4)

    md_path = os.path.join(session_dir, "judge_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Judge Agent Report\n\n")
        f.write(f"**Status:** {scorecard.status}\n")
        f.write(f"**Overall Score:** {scorecard.overall_score}\n\n")

        f.write("## Sub Scores\n")
        for k, v in subs.model_dump().items():
            f.write(f"- **{k.replace('_',' ').title()}:** {v}\n")

        f.write("\n## Issues\n")
        if not issues:
            f.write("No issues found.\n")
        else:
            for issue in issues:
                f.write(f"\n### {issue.id} — {issue.severity.upper()}\n")
                f.write(f"**Sentence Index:** {issue.location_in_letter.get('sentence_index')}\n")
                f.write(f"**Description:** {issue.description}\n")
                if issue.evidence_refs:
                    f.write(f"**Evidence Refs:** {', '.join(issue.evidence_refs)}\n")

    logger.info("[Judge] Completed successfully.")
    return scorecard
