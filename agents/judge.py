# agents/judge.py
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import json
import re
import difflib
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ============================================================
# Pydantic Models
# ============================================================
class Issue(BaseModel):
    id: str
    severity: str = Field(..., description='"low" | "medium" | "high"')
    location_in_letter: Optional[Dict] = None
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
    overall_score: int = Field(..., ge=0, le=100)
    status: str
    sub_scores: SubScores
    issues: List[Issue]
    confidence_estimate: float = Field(..., ge=0.0, le=1.0)
    meta: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    def compute_overall(cls, values):
        if "overall_score" not in values:
            subs = values.get("sub_scores")
            if not subs:
                return values

            if isinstance(subs, SubScores):
                v = subs.model_dump()
            else:
                v = subs

            overall = int(
                (
                    v["factual_accuracy"]
                    + v["citation_consistency"]
                    + v["logical_adequacy"]
                    + v["tone_professionalism"]
                    - v["hallucination_risk"]
                )
                / 5
            )
            values["overall_score"] = overall
            values["status"] = "approve" if overall >= 85 else "needs_revision"

        return values


# ============================================================
# Loaders
# ============================================================
def load_json(path):
    if not os.path.exists(path):
        logger.warning(f"[Judge] Missing JSON: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[Judge] Failed to load JSON {path}: {e}")
        return None


def load_text(path):
    if not os.path.exists(path):
        logger.warning(f"[Judge] Missing text: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"[Judge] Failed to load text {path}: {e}")
        return None


def load_all_inputs(session_dir):
    return {
        "auditor": load_json(os.path.join(session_dir, "auditor_output.json")),
        "clinician": load_json(os.path.join(session_dir, "clinician_output.json")),
        "regulatory": load_json(os.path.join(session_dir, "regulatory_output.json")),
        "barrister": load_text(os.path.join(session_dir, "barrister_output.txt")),
    }


# ============================================================
# Helpers
# ============================================================
def split_into_sentences(text):
    if not text:
        return []

    text = re.sub(r"[\\r\\n]+", " ", text)
    parts = re.split(r"(?<=[.!?])\\s+(?=[A-Z0-9\\[]) ", text)

    return [s.strip() for s in parts if s.strip()]


def identify_claim_sentences(sentences):
    claim_keywords = [
        "evidence", "clinical", "study", "research", "medically necessary",
        "medical necessity", "denial", "policy", "regulation",
        "coverage", "required", "should be covered", "support",
        "effective", "beneficial", "recommended", "indicated",
        "dispute", "argue", "counter"
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


def link_evidence_to_claim(sentence, auditor, clinician, regulatory):
    s = sentence.lower()
    matches = {"auditor": [], "clinician": [], "regulatory": []}

    # ---------------- AUDITOR ----------------
    if auditor:
        for chunk in auditor.get("raw_evidence_chunks", []):
            try:
                ratio = difflib.SequenceMatcher(None, s, chunk.lower()).ratio()
                if ratio > 0.35:
                    matches["auditor"].append(chunk[:50])
            except:
                pass

        # denial code match
        dc = auditor.get("denial_code", "").lower()
        if dc and dc in s:
            matches["auditor"].append(f"DenialCode:{dc}")

        snippet = (auditor.get("insurer_reason_snippet") or "").lower()
        if snippet:
            words = snippet.split()[:4]
            if any(w in s for w in words):
                matches["auditor"].append("InsurerReasonSnippet")


    # ---------------- CLINICIAN ----------------
    if clinician and isinstance(clinician, dict):
        for entry in clinician.get("root", []):
            title = (entry.get("article_title") or "").lower()
            summary = (entry.get("summary_of_finding") or "").lower()
            pmid = entry.get("pubmed_id", "").lower()

            combined = f"{title} {summary} {pmid}"

            ratio = difflib.SequenceMatcher(None, s, combined).ratio()
            if pmid and pmid in s:
                ratio = 1.0

            if ratio > 0.25:
                matches["clinician"].append(f"PMID:{pmid or 'unknown'}")


    # ---------------- REGULATORY ----------------
    if regulatory and isinstance(regulatory, dict):
        legal_points = regulatory.get("legal_points", [])
        if isinstance(legal_points, list):
            for lp in legal_points:
                statute = (lp.get("statute") or lp.get("reference") or "unknown").lower()
                summary = (lp.get("summary") or lp.get("argument") or "").lower()

                if statute in s or difflib.SequenceMatcher(None, s, summary).ratio() > 0.20:
                    matches["regulatory"].append(statute)
        else:
            combined = ""
            for key in ("argument", "action", "violation"):
                if isinstance(regulatory.get(key), str):
                    combined += regulatory[key] + " "

            if combined.strip():
                ratio = difflib.SequenceMatcher(None, s, combined.lower()).ratio()
                if ratio > 0.18:
                    matches["regulatory"].append("RegulatorySummary")

    return matches


# ============================================================
# Scoring
# ============================================================
def score_claim_evidence(matches):
    score = 0
    details = []

    if matches["auditor"]:
        score += 20
        details.append("Auditor evidence matched")

    if matches["clinician"]:
        score += 40
        details.append("Clinical evidence matched")

    if matches["regulatory"]:
        score += 40
        details.append("Regulatory evidence matched")

    if score == 0:
        details.append("No evidence matched")

    return score, details


def compute_overall_scores(claim_results):
    claims = [c for c in claim_results if c["label"] == "CLAIM"]
    if not claims:
        return {
            "factual_accuracy": 95,
            "citation_consistency": 95,
            "logical_adequacy": 95,
            "tone_professionalism": 90,
            "hallucination_risk": 0
        }

    supported = sum(1 for c in claims if c["score"] >= 30)
    hallucinations = sum(1 for c in claims if c["score"] == 0)

    factual = int((supported / len(claims)) * 100)
    halluc = int((hallucinations / len(claims)) * 100)

    return {
        "factual_accuracy": factual,
        "citation_consistency": factual,
        "logical_adequacy": factual,
        "tone_professionalism": 90,
        "hallucination_risk": halluc,
    }


def detect_issues(claim_results):
    issues = []
    counter = 1

    for c in claim_results:
        if c["label"] != "CLAIM":
            continue

        score = c["score"]

        # ---------------- UNSUPPORTED ----------------
        if score == 0:
            issues.append(Issue(
                id=f"ISSUE-{counter}",
                severity="high",
                location_in_letter={"sentence_index": c["sentence_index"]},
                description=f"Unsupported claim: '{c['sentence']}'",
                evidence_refs=[],
                suggested_fix="Add clinical/regulatory evidence or remove the claim."
            ))
            counter += 1
            continue

        # ---------------- PARTIALLY SUPPORTED ----------------
        missing = []
        if not c["matches"]["clinician"]:
            missing.append("clinical evidence")
        if not c["matches"]["regulatory"]:
            missing.append("regulatory evidence")

        if missing:
            refs = []
            for src, lst in c["matches"].items():
                if lst:
                    refs.extend(lst)

            issues.append(Issue(
                id=f"ISSUE-{counter}",
                severity="medium",
                location_in_letter={"sentence_index": c["sentence_index"]},
                description=f"Partially supported claim. Missing: {', '.join(missing)}",
                evidence_refs=list(set(refs)),
                suggested_fix="Strengthen the argument by adding missing evidence."
            ))
            counter += 1

    return issues


# ============================================================
# Main Pipeline
# ============================================================
def run_judge_agent(session_dir="data/output/"):
    logger.info("[Judge] Loading inputs...")
    inputs = load_all_inputs(session_dir)

    auditor = inputs["auditor"]
    clinician = inputs["clinician"]
    regulatory = inputs["regulatory"]
    letter = inputs["barrister"]

    if not letter:
        logger.error("[Judge] No appeal letter found.")
        return None

    sentences = split_into_sentences(letter)
    label_data = identify_claim_sentences(sentences)

    claim_results = []
    for entry in label_data:
        s = entry["sentence"]
        if entry["label"] == "CLAIM":
            matches = link_evidence_to_claim(s, auditor, clinician, regulatory)
            score, details = score_claim_evidence(matches)
        else:
            matches, score, details = {"auditor": [], "clinician": [], "regulatory": []}, 0, ["Non-claim"]

        claim_results.append({
            "sentence_index": entry["sentence_index"],
            "sentence": s,
            "label": entry["label"],
            "matches": matches,
            "score": score,
            "score_details": details
        })

    subscores = SubScores(**compute_overall_scores(claim_results))
    issues = detect_issues(claim_results)

    scorecard = JudgeScorecard(
        sub_scores=subscores,
        issues=issues,
        confidence_estimate=0.85,
        meta={"generated_at": datetime.utcnow().isoformat(), "version": "v1.3"}
    )

    # ---------------- SAVE JSON ----------------
    os.makedirs(session_dir, exist_ok=True)
    json_path = os.path.join(session_dir, "judge_scorecard.json")
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(scorecard.model_dump(), indent=4))
        logger.info(f"[Judge] Scorecard saved to {json_path}")
    except Exception as e:
        logger.error(f"[Judge] Failed to save JSON: {e}")

    # ---------------- SAVE MARKDOWN ----------------
    md_path = os.path.join(session_dir, "judge_report.md")
    try:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# Judge Agent Report\n\n")
            f.write(f"**Status:** {scorecard.status}\n")
            f.write(f"**Overall Score:** {scorecard.overall_score}\n\n")

            f.write("## Sub Scores\n")
            for k, v in subscores.model_dump().items():
                f.write(f"- **{k.title().replace('_', ' ')}:** {v}\n")

            f.write("\n## Issues\n")
            if not issues:
                f.write("No issues found.\n")
            else:
                for issue in issues:
                    f.write(f"\n### {issue.id} — {issue.severity.upper()}\n")
                    f.write(f"**Description:** {issue.description}\n")
                    f.write(f"**Sentence Index:** {issue.location_in_letter.get('sentence_index')}\n")
                    if issue.evidence_refs:
                        f.write(f"**Evidence Refs:** {', '.join(issue.evidence_refs)}\n")
    except Exception as e:
        logger.error(f"[Judge] Failed to save MD: {e}")

    logger.info("[Judge] Completed successfully.")
    return scorecard
