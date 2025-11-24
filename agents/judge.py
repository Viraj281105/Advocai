from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime



class Issue(BaseModel):
    id: str
    severity: str                     # "low" | "medium" | "high"
    location_in_letter: Optional[Dict] = None   # e.g., {"sentence_index": 3}
    description: str
    evidence_refs: Optional[List[str]] = None
    suggested_fix: Optional[str] = None


class SubScores(BaseModel):
    factual_accuracy: int
    citation_consistency: int
    logical_adequacy: int
    tone_professionalism: int
    hallucination_risk: int


class JudgeScorecard(BaseModel):
    overall_score: int
    status: str                       # "approve" | "needs_revision"
    sub_scores: SubScores
    issues: List[Issue]
    confidence_estimate: float
    meta: Optional[Dict] = None

import os
import json


# ---------- File Loader Helpers ----------

def load_json(path: str):
    """Safely load a JSON file. Returns None if missing."""
    if not os.path.exists(path):
        print(f"[WARNING] Missing file: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load {path}: {e}")
        return None


def load_text(path: str):
    """Safely load a text file. Returns None if missing."""
    if not os.path.exists(path):
        print(f"[WARNING] Missing file: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"[ERROR] Failed to load {path}: {e}")
        return None


# ---------- Main Loader for Judge Agent ----------

def load_all_inputs(session_dir: str):
    """
    Loads all necessary outputs from other agents.
    session_dir = folder like data/output/
    """

    auditor_path = os.path.join(session_dir, "auditor_output.json")
    clinician_path = os.path.join(session_dir, "clinician_output.json")
    regulatory_path = os.path.join(session_dir, "regulatory_output.json")
    barrister_path = os.path.join(session_dir, "barrister_output.txt")

    return {
        "auditor": load_json(auditor_path),
        "clinician": load_json(clinician_path),
        "regulatory": load_json(regulatory_path),
        "barrister": load_text(barrister_path),
    }


import re

# ---------- Sentence Splitting Helper ----------

def split_into_sentences(text: str):
    """
    Splits the final appeal letter into clean, indexed sentences.
    Returns a list of sentences.
    """
    if not text:
        return []

    # Basic sentence splitter
    raw_sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    # Clean & remove empty sentences
    sentences = [s.strip() for s in raw_sentences if s.strip()]

    return sentences

# ---------- Claim Detection Helper ----------

def identify_claim_sentences(sentences: list):
    """
    Labels sentences as CLAIM or NON-CLAIM using simple keyword heuristics.
    Returns a list of dict: {sentence, label}
    """
    claim_keywords = [
        "evidence",
        "clinical",
        "study",
        "research",
        "medically necessary",
        "treatment",
        "denial",
        "policy",
        "regulation",
        "coverage",
        "required",
        "should be covered",
        "support",
        "effective",
        "beneficial"
    ]

    results = []

    for index, sentence in enumerate(sentences):
        sentence_lower = sentence.lower()

        # Check if any keyword appears in sentence
        is_claim = any(kw in sentence_lower for kw in claim_keywords)

        results.append({
            "sentence_index": index,
            "sentence": sentence,
            "label": "CLAIM" if is_claim else "NON_CLAIM"
        })

    return results

import difflib

# ---------- Evidence Linking Helper ----------

def link_evidence_to_claim(sentence: str, auditor, clinician, regulatory):
    """
    Attempts to link a claim sentence to clinical, legal, and denial evidence.
    Returns a dict with evidence matches.
    """

    sentence_lower = sentence.lower()

    matches = {
        "auditor": [],
        "clinician": [],
        "regulatory": []
    }


    # ----- 1. Match with Auditor evidence (denial information) -----
    if auditor:
        # Raw evidence chunks (text extracted from PDF)
        raw_chunks = auditor.get("raw_evidence_chunks", [])
        for chunk in raw_chunks:
            ratio = difflib.SequenceMatcher(None, sentence_lower, chunk.lower()).ratio()
            if ratio > 0.25:     # simple fuzzy match threshold
                matches["auditor"].append(chunk)

        # Match denial code or keywords
        denial_code = auditor.get("denial_code", "")
        if denial_code.lower() in sentence_lower:
            matches["auditor"].append(f"[Matched denial code: {denial_code}]")

    # ----- 2. Match with Clinician evidence (PubMed abstracts) -----
    if clinician and "evidence" in clinician:
        for entry in clinician["evidence"]:
            abstract = entry.get("abstract", "")
            ratio = difflib.SequenceMatcher(None, sentence_lower, abstract.lower()).ratio()
            if ratio > 0.20:
                matches["clinician"].append(f"PMID:{entry.get('pmid')}")

    # ----- 3. Match with Regulatory evidence (legal leverage) -----
    if regulatory and "legal_points" in regulatory:
        for entry in regulatory["legal_points"]:
            summary = entry.get("summary", "")
            ratio = difflib.SequenceMatcher(None, sentence_lower, summary.lower()).ratio()
            if ratio > 0.20:
                matches["regulatory"].append(entry.get("statute"))

    return matches

# ---------- Scoring Engine ----------

def score_claim_evidence(matches: dict):
    """
    Scores a single claim based on how much evidence supports it.
    Hybrid scoring: simple + ready for advanced additions.
    """
    score = 0
    details = []

    # ----- Auditor evidence (denial match) -----
    if matches["auditor"]:
        score += 30
        details.append("Matched denial evidence")

    # ----- Clinician evidence (medical) -----
    if matches["clinician"]:
        score += 30
        details.append("Matched clinical evidence")

    # ----- Regulatory evidence (legal) -----
    if matches["regulatory"]:
        score += 30
        details.append("Matched legal evidence")

    # ----- Partial credit -----
    if score == 0:
        # No evidence → high hallucination risk later
        details.append("No supporting evidence found")

    return score, details


def compute_overall_scores(claim_results: list):
    """
    Aggregates claim-level scores to produce:
    - factual accuracy
    - citation consistency
    - logical adequacy
    - tone professionalism (placeholder)
    - hallucination risk
    """

    total_claims = len(claim_results)
    supported_claims = 0
    citation_issues = 0
    hallucinations = 0

    for result in claim_results:
        if result["score"] >= 30:
            supported_claims += 1
        if result["score"] == 0:
            hallucinations += 1

    if total_claims == 0:
        factual_accuracy = 100
        hallucination_risk = 0
    else:
        factual_accuracy = int((supported_claims / total_claims) * 100)
        hallucination_risk = int((hallucinations / total_claims) * 100)

    # Placeholder values — will refine in Step 8
    citation_consistency = factual_accuracy
    logical_adequacy = factual_accuracy
    tone_professionalism = 90

    return {
        "factual_accuracy": factual_accuracy,
        "citation_consistency": citation_consistency,
        "logical_adequacy": logical_adequacy,
        "tone_professionalism": tone_professionalism,
        "hallucination_risk": hallucination_risk
    }


# ---------- Issue Detection Engine ----------

def detect_issues(claim_results: list):
    """
    Creates a list of issues based on unsupported claims,
    missing citations, and hallucination risks.
    """

    issues = []
    issue_counter = 1

    for claim in claim_results:

        # Case 1: No evidence supports the claim
        if claim["score"] == 0:
            issues.append({
                "id": f"ISSUE-{issue_counter}",
                "severity": "high",
                "location_in_letter": {"sentence_index": claim["sentence_index"]},
                "description": f"Unsupported claim: '{claim['sentence']}'",
                "evidence_refs": [],
                "suggested_fix": "Add clinical, legal, or denial evidence to support this claim."
            })
            issue_counter += 1

        # Case 2: Partial support, but missing legal or clinical evidence
        elif claim["score"] == 30 or claim["score"] == 60:
            missing = []
            if not claim["matches"]["auditor"]:
                missing.append("denial evidence")
            if not claim["matches"]["clinician"]:
                missing.append("clinical evidence")
            if not claim["matches"]["regulatory"]:
                missing.append("legal evidence")

            # Flatten evidence
            evidence_list = []
            for source, items in claim["matches"].items():
                if items:
                    for it in items:
                        evidence_list.append(str(it))

            issues.append({
                "id": f"ISSUE-{issue_counter}",
                "severity": "medium",
                "location_in_letter": {"sentence_index": claim["sentence_index"]},
                "description": f"Partially supported claim: '{claim['sentence']}'. Missing: {', '.join(missing)}.",
                "evidence_refs": evidence_list,
                "suggested_fix": "Strengthen this claim by citing the missing evidence sources."
            })
            issue_counter += 1

    return issues

# ---------- Main Judge Agent Pipeline ----------

def run_judge_agent(session_dir="data/output/"):
    """
    The full pipeline that:
    - loads agent outputs
    - processes the letter
    - scores everything
    - generates a final scorecard
    """

    print("\n[Judge Agent] Loading inputs...")
    inputs = load_all_inputs(session_dir)

    auditor = inputs["auditor"]
    clinician = inputs["clinician"]
    regulatory = inputs["regulatory"]
    letter = inputs["barrister"]

    if not letter:
        print("[ERROR] No final appeal letter found. Cannot run Judge Agent.")
        return None

    # ----- Step 1: Sentence splitting -----
    sentences = split_into_sentences(letter)

    # ----- Step 2: Claim detection -----
    claim_data = identify_claim_sentences(sentences)

    # ----- Step 3: Evidence linking -----
    claim_results = []
    for entry in claim_data:
        matches = link_evidence_to_claim(
            entry["sentence"],
            auditor,
            clinician,
            regulatory
        )
        score, details = score_claim_evidence(matches)

        claim_results.append({
            "sentence_index": entry["sentence_index"],
            "sentence": entry["sentence"],
            "label": entry["label"],
            "matches": matches,
            "score": score,
            "score_details": details
        })

    # ----- Step 4: Compute global scores -----
    subscore_values = compute_overall_scores(claim_results)

    subscores = SubScores(
        factual_accuracy=subscore_values["factual_accuracy"],
        citation_consistency=subscore_values["citation_consistency"],
        logical_adequacy=subscore_values["logical_adequacy"],
        tone_professionalism=subscore_values["tone_professionalism"],
        hallucination_risk=subscore_values["hallucination_risk"]
    )

    # ----- Step 5: Issue detection -----
    issues_raw = detect_issues(claim_results)
    issues = [Issue(**issue) for issue in issues_raw]

    # ----- Step 6: Final score -----
    overall_score = int(
        (subscores.factual_accuracy +
         subscores.citation_consistency +
         subscores.logical_adequacy +
         subscores.tone_professionalism -
         subscores.hallucination_risk) / 5
    )

    status = "approve" if overall_score >= 85 else "needs_revision"

    # ----- Step 7: Build Scorecard -----
    scorecard = JudgeScorecard(
        overall_score=overall_score,
        status=status,
        sub_scores=subscores,
        issues=issues,
        confidence_estimate=0.85,
        meta={
            "generated_at": datetime.utcnow().isoformat(),
            "judge_agent_version": "v1.0"
        }
    )

    # ----- Step 8: Save JSON output -----
    json_path = f"{session_dir}/judge_scorecard.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(scorecard.json(indent=4))


    print(f"[Judge Agent] Scorecard saved at: {json_path}")

    # ----- Step 9: Save Markdown report -----
    md_path = f"{session_dir}/judge_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Judge Agent Report\n\n")
        f.write(f"**Status:** {status}\n\n")
        f.write(f"**Overall Score:** {overall_score}\n\n")

        f.write("## Sub Scores:\n")
        for name, value in subscore_values.items():
            f.write(f"- **{name.replace('_',' ').title()}:** {value}\n")

        f.write("\n## Issues:\n")
        if not issues:
            f.write("No issues found.\n")
        else:
            for issue in issues:
                f.write(f"\n### {issue.id}\n")
                f.write(f"- **Severity:** {issue.severity}\n")
                f.write(f"- **Sentence Index:** {issue.location_in_letter}\n")
                f.write(f"- **Description:** {issue.description}\n")
                f.write(f"- **Suggested Fix:** {issue.suggested_fix}\n")
                f.write(f"- **Evidence Refs:** {issue.evidence_refs}\n")

    print(f"[Judge Agent] Markdown report saved at: {md_path}")

    return scorecard



if __name__ == "__main__":
    run_judge_agent("data/output/test_case_1/")
