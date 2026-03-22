# tools/pdf_compiler.py
# Assembles all agent outputs into a single downloadable PDF appeal packet
# Uses only stdlib + reportlab (pip install reportlab)

import json
import os
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY


# ── Colour palette ────────────────────────────────────────────────────────
PURPLE      = colors.HexColor("#4f31b8")
PURPLE_LIGHT= colors.HexColor("#ede8fd")
GOLD        = colors.HexColor("#c9a84c")
DARK        = colors.HexColor("#1a1040")
MUTED       = colors.HexColor("#6b7280")
RED_LIGHT   = colors.HexColor("#fef2f2")
RED         = colors.HexColor("#dc2626")
GREEN_LIGHT = colors.HexColor("#f0fdf4")
GREEN       = colors.HexColor("#16a34a")
AMBER_LIGHT = colors.HexColor("#fffbeb")
AMBER       = colors.HexColor("#d97706")
BORDER      = colors.HexColor("#e5e7eb")
WHITE       = colors.white


def _styles():
    base = getSampleStyleSheet()

    def add(name, **kw):
        if name not in base:
            base.add(ParagraphStyle(name=name, **kw))
        return base[name]

    add("CoverTitle",    fontName="Helvetica-Bold",   fontSize=28, textColor=DARK,   leading=34, alignment=TA_CENTER)
    add("CoverSub",      fontName="Helvetica",         fontSize=13, textColor=MUTED,  leading=18, alignment=TA_CENTER)
    add("CoverMeta",     fontName="Helvetica",         fontSize=11, textColor=MUTED,  leading=16, alignment=TA_CENTER)
    add("SectionHead",   fontName="Helvetica-Bold",   fontSize=14, textColor=PURPLE, leading=20, spaceAfter=6)
    add("SubHead",       fontName="Helvetica-Bold",   fontSize=11, textColor=DARK,   leading=16, spaceAfter=4)
    add("Body",          fontName="Helvetica",         fontSize=10, textColor=DARK,   leading=15, alignment=TA_JUSTIFY)
    add("BodyMono",      fontName="Courier",           fontSize=9,  textColor=DARK,   leading=13)
    add("SmallMuted",    fontName="Helvetica",         fontSize=9,  textColor=MUTED,  leading=13)
    add("LabelPurple",   fontName="Helvetica-Bold",   fontSize=9,  textColor=PURPLE, leading=13)
    add("LetterBody",    fontName="Helvetica",         fontSize=10, textColor=DARK,   leading=17, alignment=TA_JUSTIFY)
    add("ScoreGreen",    fontName="Helvetica-Bold",   fontSize=22, textColor=GREEN,  leading=26, alignment=TA_CENTER)
    add("ScoreAmber",    fontName="Helvetica-Bold",   fontSize=22, textColor=AMBER,  leading=26, alignment=TA_CENTER)
    add("ScoreRed",      fontName="Helvetica-Bold",   fontSize=22, textColor=RED,    leading=26, alignment=TA_CENTER)
    add("VerdictGreen",  fontName="Helvetica-Bold",   fontSize=13, textColor=GREEN,  leading=18, alignment=TA_CENTER)
    add("VerdictAmber",  fontName="Helvetica-Bold",   fontSize=13, textColor=AMBER,  leading=18, alignment=TA_CENTER)
    add("VerdictRed",    fontName="Helvetica-Bold",   fontSize=13, textColor=RED,    leading=18, alignment=TA_CENTER)
    return base


def _hr(story):
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 10))


def _section(story, title: str, styles):
    story.append(Spacer(1, 16))
    story.append(Paragraph(title, styles["SectionHead"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PURPLE))
    story.append(Spacer(1, 10))


def _load(case_dir: str, filename: str):
    path = Path(case_dir) / filename
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    if filename.endswith(".json"):
        try:
            return json.loads(text)
        except Exception:
            return None
    return text


# ══════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════
def compile_appeal_packet(case_dir: str, output_path: str | None = None) -> str:
    """
    Read all agent outputs from case_dir and write a PDF to output_path.
    Returns the path to the generated PDF.
    """
    if output_path is None:
        output_path = str(Path(case_dir) / "appeal_packet.pdf")

    styles   = _styles()
    story    = []
    case_id  = Path(case_dir).name
    now      = datetime.now().strftime("%B %d, %Y")

    # Load all outputs
    auditor    = _load(case_dir, "auditor_output.json")    or {}
    clinician  = _load(case_dir, "clinician_output.json")  or {}
    regulatory = _load(case_dir, "regulatory_output.json") or {}
    barrister  = _load(case_dir, "barrister_output.txt")   or ""
    scorecard  = _load(case_dir, "judge_scorecard.json")   or {}
    judge_md   = _load(case_dir, "judge_report.md")        or ""

    procedure  = auditor.get("procedure_denied", "Medical Procedure")
    denial_code= auditor.get("denial_code", "—")

    # ── PAGE 1: Cover ─────────────────────────────────────────────────────
    story.append(Spacer(1, 2*cm))

    # Logo-style header bar
    header_data = [[ Paragraph("AdvocAI", ParagraphStyle("Logo", fontName="Helvetica-Bold", fontSize=22, textColor=WHITE)),
                     Paragraph("Autonomous Insurance Appeal System", ParagraphStyle("LogoSub", fontName="Helvetica", fontSize=11, textColor=colors.HexColor("#c4b5fd"))) ]]
    header_table = Table(header_data, colWidths=["30%","70%"])
    header_table.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), PURPLE),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 16),
        ("RIGHTPADDING",(0,0), (-1,-1), 16),
        ("TOPPADDING",  (0,0), (-1,-1), 14),
        ("BOTTOMPADDING",(0,0),(-1,-1), 14),
        ("ROUNDEDCORNERS", (0,0), (-1,-1), 8),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 2*cm))

    story.append(Paragraph("INSURANCE APPEAL PACKET", styles["CoverSub"]))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(procedure, styles["CoverTitle"]))
    story.append(Spacer(1, 0.6*cm))
    story.append(HRFlowable(width="60%", thickness=1.5, color=GOLD, hAlign="CENTER"))
    story.append(Spacer(1, 0.6*cm))

    meta_lines = [
        f"Denial Code: <b>{denial_code}</b>",
        f"Case ID: <b>{case_id}</b>",
        f"Generated: <b>{now}</b>",
        "Prepared by: <b>AdvocAI Multi-Agent System</b>",
    ]
    for line in meta_lines:
        story.append(Paragraph(line, styles["CoverMeta"]))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 1.5*cm))

    # Contents table
    contents = [
        ["Section", "Contents"],
        ["1", "Denial Summary"],
        ["2", "Appeal Letter"],
        ["3", "Medical Evidence"],
        ["4", "Legal & Regulatory Brief"],
        ["5", "QA Scorecard"],
    ]
    tbl = Table(contents, colWidths=["15%", "85%"])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  PURPLE),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 10),
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("TEXTCOLOR",     (0,1), (-1,-1), DARK),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, PURPLE_LIGHT]),
        ("ALIGN",         (0,0), (0,-1),  "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, BORDER),
    ]))
    story.append(tbl)

    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        "⚠ This document is generated by AI for informational purposes. "
        "Review with a qualified attorney before submission.",
        ParagraphStyle("Disclaimer", fontName="Helvetica-Oblique", fontSize=8,
                       textColor=MUTED, alignment=TA_CENTER)
    ))
    story.append(PageBreak())

    # ── SECTION 1: Denial Summary ─────────────────────────────────────────
    _section(story, "Section 1 — Denial Summary", styles)

    denial_rows = [
        ["Field", "Value"],
        ["Procedure Denied",   auditor.get("procedure_denied", "—")],
        ["Denial Code",        auditor.get("denial_code", "—")],
        ["Confidence Score",   str(auditor.get("confidence_score", "—"))],
    ]
    dtbl = Table(denial_rows, colWidths=["35%","65%"])
    dtbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  PURPLE),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("FONTNAME",      (0,1), (0,-1),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 10),
        ("TEXTCOLOR",     (0,1), (-1,-1), DARK),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, PURPLE_LIGHT]),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 12),
        ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, BORDER),
    ]))
    story.append(dtbl)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Insurer's Reason", styles["SubHead"]))
    reason = auditor.get("insurer_reason_snippet", "No reason provided.")
    story.append(Paragraph(reason, styles["Body"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Policy Clause Cited", styles["SubHead"]))
    clause = auditor.get("policy_clause_text", "No clause provided.")
    story.append(Paragraph(clause[:800] + ("..." if len(clause) > 800 else ""), styles["Body"]))

    story.append(PageBreak())

    # ── SECTION 2: Appeal Letter ──────────────────────────────────────────
    _section(story, "Section 2 — Appeal Letter", styles)

    if barrister.strip():
        for para in barrister.split("\n\n"):
            para = para.strip()
            if not para:
                continue
            # Strip markdown bold markers for PDF
            para = para.replace("**", "").replace("###", "").replace("##", "").replace("#", "")
            para = para.encode("ascii", "ignore").decode("ascii")
            story.append(Paragraph(para, styles["LetterBody"]))
            story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("Appeal letter not yet generated.", styles["Body"]))

    story.append(PageBreak())

    # ── SECTION 3: Medical Evidence ───────────────────────────────────────
    _section(story, "Section 3 — Medical Evidence (PubMed)", styles)

    articles = clinician.get("root", [])
    if articles:
        for i, art in enumerate(articles, 1):
            story.append(Paragraph(f"{i}. {art.get('article_title', 'Untitled')}", styles["SubHead"]))
            if art.get("pubmed_id"):
                story.append(Paragraph(f"PMID: {art['pubmed_id']}", styles["LabelPurple"]))
            summary = art.get("summary_of_finding") or art.get("summary") or art.get("abstract", "")
            if summary:
                story.append(Paragraph(summary, styles["Body"]))
            story.append(Spacer(1, 10))
    else:
        # Clinician returned empty — note why
        box_data = [[Paragraph(
            "No PubMed articles were retrieved for this case. This may be because the "
            "Clinician agent did not find matching studies, or because the case was run "
            "without a live PubMed API connection. Strengthening this section with peer-reviewed "
            "evidence is recommended before submission.",
            styles["Body"]
        )]]
        box = Table(box_data, colWidths=["100%"])
        box.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), AMBER_LIGHT),
            ("BOX",           (0,0), (-1,-1), 0.5, AMBER),
            ("LEFTPADDING",   (0,0), (-1,-1), 14),
            ("RIGHTPADDING",  (0,0), (-1,-1), 14),
            ("TOPPADDING",    (0,0), (-1,-1), 10),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ]))
        story.append(box)

    story.append(PageBreak())

    # ── SECTION 4: Regulatory Brief ───────────────────────────────────────
    _section(story, "Section 4 — Legal & Regulatory Brief", styles)

    compliant   = regulatory.get("compliant", None)
    violation   = regulatory.get("violation", "")
    argument    = regulatory.get("argument", "")
    action      = regulatory.get("action", "")
    legal_points= regulatory.get("legal_points", [])

    # Compliance status badge
    if compliant is False:
        badge_bg, badge_fg, badge_text = RED_LIGHT, RED, "NON-COMPLIANT — Denial appears to violate applicable regulations"
    elif compliant is True:
        badge_bg, badge_fg, badge_text = GREEN_LIGHT, GREEN, "COMPLIANT — No regulatory violations detected"
    else:
        badge_bg, badge_fg, badge_text = AMBER_LIGHT, AMBER, "UNDER REVIEW — Compliance status requires manual review"

    badge_data = [[Paragraph(badge_text, ParagraphStyle("Badge", fontName="Helvetica-Bold",
                   fontSize=10, textColor=badge_fg))]]
    badge_tbl = Table(badge_data, colWidths=["100%"])
    badge_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), badge_bg),
        ("BOX",          (0,0),(-1,-1), 1, badge_fg),
        ("LEFTPADDING",  (0,0),(-1,-1), 14),
        ("TOPPADDING",   (0,0),(-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
    ]))
    story.append(badge_tbl)
    story.append(Spacer(1, 12))

    if violation and violation != "UNPARSABLE_JSON":
        story.append(Paragraph("Violation Identified", styles["SubHead"]))
        story.append(Paragraph(violation, styles["Body"]))
        story.append(Spacer(1, 8))

    if argument:
        story.append(Paragraph("Legal Argument", styles["SubHead"]))
        # argument may itself contain nested JSON string — clean it up
        arg_text = argument if isinstance(argument, str) else json.dumps(argument, indent=2)
        arg_text = arg_text[:1200] + ("..." if len(arg_text) > 1200 else "")
        story.append(Paragraph(arg_text, styles["Body"]))
        story.append(Spacer(1, 8))

    if action:
        story.append(Paragraph(f"Recommended Action: {action}", styles["LabelPurple"]))
        story.append(Spacer(1, 8))

    if legal_points:
        story.append(Paragraph("Applicable Statutes", styles["SubHead"]))
        for pt in legal_points:
            story.append(Paragraph(f"• <b>{pt.get('statute','')}</b> — {pt.get('summary','')}", styles["Body"]))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph(
            "No specific statutes were parsed in this run. Manual regulatory review recommended.",
            styles["SmallMuted"]
        ))

    story.append(PageBreak())

    # ── SECTION 5: Judge Scorecard ────────────────────────────────────────
    _section(story, "Section 5 — QA Scorecard (Judge Agent)", styles)

    overall      = scorecard.get("overall_score", 0)
    status       = scorecard.get("status", "unknown")
    sub_scores   = scorecard.get("sub_scores", {})
    issues       = scorecard.get("issues", [])
    confidence   = scorecard.get("confidence_estimate", 0)

    # Overall score display
    if overall >= 70:
        score_style, verdict_style = "ScoreGreen", "VerdictGreen"
    elif overall >= 40:
        score_style, verdict_style = "ScoreAmber", "VerdictAmber"
    else:
        score_style, verdict_style = "ScoreRed", "VerdictRed"

    score_data = [
        [Paragraph(str(overall), styles[score_style]),
         Paragraph(status.replace("_"," ").upper(), styles[verdict_style])],
        [Paragraph("Overall Score / 100", styles["SmallMuted"]),
         Paragraph(f"Confidence: {int(confidence*100)}%", styles["SmallMuted"])],
    ]
    score_tbl = Table(score_data, colWidths=["50%","50%"])
    score_tbl.setStyle(TableStyle([
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("BOX",           (0,0),(-1,-1), 0.5, BORDER),
        ("LINEBEFORE",    (1,0),(1,-1),  0.5, BORDER),
    ]))
    story.append(score_tbl)
    story.append(Spacer(1, 16))

    # Sub scores table
    if sub_scores:
        story.append(Paragraph("Score Breakdown", styles["SubHead"]))
        sub_rows = [["Metric", "Score"]]
        for k, v in sub_scores.items():
            label = k.replace("_", " ").title()
            sub_rows.append([label, str(v)])
        sub_tbl = Table(sub_rows, colWidths=["70%","30%"])
        sub_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0),  PURPLE),
            ("TEXTCOLOR",     (0,0),(-1,0),  WHITE),
            ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
            ("FONTNAME",      (0,1),(-1,-1), "Helvetica"),
            ("FONTSIZE",      (0,0),(-1,-1), 10),
            ("TEXTCOLOR",     (0,1),(-1,-1), DARK),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, PURPLE_LIGHT]),
            ("ALIGN",         (1,0),(1,-1),  "CENTER"),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0),(-1,-1), 7),
            ("BOTTOMPADDING", (0,0),(-1,-1), 7),
            ("LEFTPADDING",   (0,0),(-1,-1), 12),
            ("BOX",           (0,0),(-1,-1), 0.5, BORDER),
            ("INNERGRID",     (0,0),(-1,-1), 0.3, BORDER),
        ]))
        story.append(sub_tbl)
        story.append(Spacer(1, 14))

    # Issues
    if issues:
        story.append(Paragraph("Issues Flagged", styles["SubHead"]))
        for issue in issues:
            sev = issue.get("severity","").upper()
            if sev == "HIGH":
                sev_hex = "dc2626"
            elif sev == "MEDIUM":
                sev_hex = "d97706"
            else:
                sev_hex = "6b7280"
            story.append(Paragraph(
                f'<font color="#{sev_hex}"><b>[{sev}]</b></font> '
                f'{issue.get("id","")} — {issue.get("description","")}',
                styles["Body"]
            ))
            fix = issue.get("suggested_fix","")
            if fix:
                story.append(Paragraph(f"Fix: {fix}", styles["SmallMuted"]))
            story.append(Spacer(1, 6))

    # Raw judge markdown if available
    if judge_md.strip():
        _hr(story)
        story.append(Paragraph("Full Judge Report", styles["SubHead"]))
        for line in judge_md.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 4))
                continue
            line = line.lstrip("#").strip()
            story.append(Paragraph(line, styles["SmallMuted"]))

    # ── Footer note ───────────────────────────────────────────────────────
    story.append(Spacer(1, 1.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"Generated by AdvocAI on {now} · Case ID: {case_id} · MIT License · "
        "This document is AI-generated and should be reviewed by a qualified professional.",
        ParagraphStyle("Footer", fontName="Helvetica-Oblique", fontSize=8,
                       textColor=MUTED, alignment=TA_CENTER)
    ))

    # ── Build PDF ─────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title=f"AdvocAI Appeal Packet — {procedure}",
        author="AdvocAI",
    )
    doc.build(story)
    return output_path


# ── CLI usage: python tools/pdf_compiler.py data/output/case_1 ───────────
if __name__ == "__main__":
    import sys
    case_dir = sys.argv[1] if len(sys.argv) > 1 else "data/output/case_1"
    out = compile_appeal_packet(case_dir)
    print(f"PDF written to: {out}")