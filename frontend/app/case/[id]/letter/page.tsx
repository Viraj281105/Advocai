"use client";
import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  Scale, Copy, Check, Download, ChevronDown, ChevronUp,
  BookOpen, Gavel, ExternalLink
} from "lucide-react";

const MOCK_LETTER = `Dear Appeals Review Board,

This letter constitutes a formal appeal on behalf of the patient regarding the denial of coverage for Genomic Sequencing (CPT Code 81455), as communicated in the denial notice dated March 15, 2026.

STATEMENT OF MEDICAL NECESSITY

The treating physician, in accordance with established clinical protocols, determined that Genomic Sequencing is medically necessary for this patient's diagnosis and treatment planning. The denial, citing CO-50 ("not medically necessary"), is not supported by the current clinical evidence or applicable coverage mandates.

CLINICAL EVIDENCE

A comprehensive review of peer-reviewed literature supports the medical necessity of this procedure:

1. Smith et al. (2024), NEJM — "Genomic sequencing demonstrated a 43% improvement in treatment selection accuracy for patients with complex oncological profiles." (PMID: 38291045)

2. Johnson & Patel (2023), JAMA Oncology — "Targeted therapy guided by genomic profiling reduced adverse events by 31% compared to empirical treatment." (PMID: 37841203)

3. Williams et al. (2024), Nature Medicine — "Clinical utility of comprehensive genomic profiling is now established across 14 tumor types per NCCN guidelines." (PMID: 38102847)

LEGAL AND REGULATORY BASIS

The denial is inconsistent with applicable federal and state law:

1. ACA Section 2713 mandates coverage of preventive services and evidence-based screenings without cost-sharing. Genomic sequencing for oncological risk assessment meets this standard.

2. ERISA Section 502(a) prohibits arbitrary denial of benefits. The insurer's blanket application of CO-50 without individualized clinical review constitutes an arbitrary denial.

3. The Mental Health Parity and Addiction Equity Act (MHPAEA) principles of parity apply: comparable diagnostic procedures are covered for other conditions without the restrictions applied here.

CONCLUSION

We respectfully request that [Insurer Name] overturn this denial and authorize coverage for Genomic Sequencing. The clinical evidence is clear, the medical necessity is established, and the denial conflicts with federal coverage mandates.

Should this appeal be denied, we reserve the right to pursue external review under applicable state law and federal regulations.

Respectfully submitted,
[Patient Name]
[Date]`;

const PUBMED_EVIDENCE = [
  { pmid: "38291045", title: "Genomic sequencing in complex oncological profiles: a prospective cohort study", journal: "NEJM", year: 2024, summary: "Demonstrated 43% improvement in treatment selection accuracy using comprehensive genomic profiling vs standard diagnostic workup." },
  { pmid: "37841203", title: "Targeted therapy outcomes guided by genomic profiling: a meta-analysis", journal: "JAMA Oncology", year: 2023, summary: "Reduced adverse treatment events by 31% and improved progression-free survival by median 4.2 months in patients with solid tumors." },
  { pmid: "38102847", title: "Clinical utility of comprehensive genomic profiling across tumor types", journal: "Nature Medicine", year: 2024, summary: "Established clinical utility across 14 tumor types per NCCN guidelines; 67% of patients received actionable findings." },
];

const STATUTES = [
  { name: "ACA §2713", full: "Affordable Care Act Section 2713", summary: "Mandates coverage of evidence-based preventive services without cost-sharing. Genomic sequencing for oncological risk assessment qualifies under USPSTF A/B recommendations.", violation: true },
  { name: "ERISA §502(a)", full: "Employee Retirement Income Security Act Section 502(a)", summary: "Prohibits arbitrary and capricious denial of benefits. Blanket CO-50 denial without individualized clinical review violates this standard.", violation: true },
  { name: "MHPAEA", full: "Mental Health Parity and Addiction Equity Act", summary: "Parity principles extend to comparable diagnostic procedures; restrictions applied here exceed those applied to similar procedures in other disease categories.", violation: false },
];

const SCORES = [
  { label: "Clinical alignment", value: 0.91, color: "#34d399" },
  { label: "Legal compliance", value: 0.88, color: "#60a5fa" },
  { label: "Structure integrity", value: 1.0,  color: "#8b6fe8" },
  { label: "Hallucination score", value: 0.04, color: "#fbbf24", invert: true },
];

export default function LetterPage() {
  const params = useParams();
  const sessionId = params.id as string;
  const [copied, setCopied] = useState(false);
  const [evidenceOpen, setEvidenceOpen] = useState(true);
  const [statutesOpen, setStatutesOpen] = useState(true);

  const copyLetter = () => {
    navigator.clipboard.writeText(MOCK_LETTER);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const overallScore = Math.round(
    ((0.91 + 0.88 + 1.0 + (1 - 0.04)) / 4) * 100
  );

  return (
    <div className="min-h-screen" style={{ background: "var(--purple-950)" }}>
      <div className="orb orb-1 fixed" style={{ opacity: 0.3 }} />

      {/* Header */}
      <header
        className="relative z-10 flex items-center justify-between px-8 py-5"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
      >
        <Link href="/" className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{ background: "linear-gradient(135deg, #4f31b8, #8b6fe8)" }}>
            <Scale size={14} color="white" />
          </div>
          <span style={{ fontFamily: "var(--font-display)", fontSize: "1.1rem" }}>
            Advo<span className="gold-text">AI</span>
          </span>
        </Link>
        <div className="flex items-center gap-3">
          <button
            onClick={copyLetter}
            className="btn-secondary flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium cursor-pointer"
            style={{ color: "rgba(250,248,242,0.6)" }}
          >
            {copied ? <Check size={13} color="#34d399" /> : <Copy size={13} />}
            {copied ? "Copied!" : "Copy letter"}
          </button>
          <button
            className="btn-primary flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium text-white cursor-pointer"
          >
            <Download size={13} />
            <span>Download packet</span>
          </button>
        </div>
      </header>

      <main className="relative z-10 max-w-6xl mx-auto px-8 py-10">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Left — Letter */}
          <div className="lg:col-span-2 flex flex-col gap-6 min-w-0">
            <div>
              <p className="text-xs uppercase tracking-widest font-medium mb-2"
                style={{ color: "var(--purple-400)" }}>Appeal letter</p>
              <h1 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(1.5rem, 3vw, 2rem)", lineHeight: 1.15 }}>
                Your appeal is <span className="gradient-text">ready to send.</span>
              </h1>
            </div>

          <div className="rounded-2xl p-8"
            style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}>
            <div
              style={{
                fontFamily: "Georgia, 'Times New Roman', serif",
                fontSize: "14px",
                lineHeight: 1.9,
                color: "rgba(250,248,242,0.8)",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                overflowX: "hidden",
                width: "100%",
                minWidth: 0,
                padding: "0 0.5rem",
              }}
            >
              {MOCK_LETTER}
            </div>
          </div>

            {/* Evidence explorer */}
            <div className="rounded-2xl overflow-hidden"
              style={{ border: "1px solid rgba(255,255,255,0.07)" }}>
              <button
                onClick={() => setEvidenceOpen((o) => !o)}
                className="w-full flex items-center justify-between px-6 py-4 cursor-pointer transition-colors"
                style={{ background: "rgba(255,255,255,0.03)" }}
              >
                <div className="flex items-center gap-3">
                  <BookOpen size={16} color="#34d399" />
                  <span className="text-sm font-medium" style={{ color: "var(--cream)" }}>
                    PubMed evidence ({PUBMED_EVIDENCE.length} articles)
                  </span>
                </div>
                {evidenceOpen ? <ChevronUp size={16} color="rgba(250,248,242,0.4)" /> : <ChevronDown size={16} color="rgba(250,248,242,0.4)" />}
              </button>
              {evidenceOpen && (
                <div className="divide-y" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
                  {PUBMED_EVIDENCE.map((art) => (
                    <div key={art.pmid} className="px-6 py-5" style={{ background: "rgba(0,0,0,0.15)" }}>
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <p className="text-sm font-medium" style={{ color: "var(--cream)" }}>
                          {art.title}
                        </p>
                        <a
                          href={`https://pubmed.ncbi.nlm.nih.gov/${art.pmid}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex-shrink-0"
                        >
                          <ExternalLink size={13} color="rgba(250,248,242,0.3)" />
                        </a>
                      </div>
                      <p className="text-xs mb-2" style={{ color: "rgba(250,248,242,0.4)" }}>
                        {art.journal} · {art.year} · PMID: {art.pmid}
                      </p>
                      <p className="text-xs leading-relaxed" style={{ color: "rgba(250,248,242,0.5)" }}>
                        {art.summary}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Statutes */}
            <div className="rounded-2xl overflow-hidden"
              style={{ border: "1px solid rgba(255,255,255,0.07)" }}>
              <button
                onClick={() => setStatutesOpen((o) => !o)}
                className="w-full flex items-center justify-between px-6 py-4 cursor-pointer"
                style={{ background: "rgba(255,255,255,0.03)" }}
              >
                <div className="flex items-center gap-3">
                  <Scale size={16} color="#fbbf24" />
                  <span className="text-sm font-medium" style={{ color: "var(--cream)" }}>
                    Legal statutes cited ({STATUTES.length})
                  </span>
                </div>
                {statutesOpen ? <ChevronUp size={16} color="rgba(250,248,242,0.4)" /> : <ChevronDown size={16} color="rgba(250,248,242,0.4)" />}
              </button>
              {statutesOpen && (
                <div className="divide-y" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
                  {STATUTES.map((s) => (
                    <div key={s.name} className="px-6 py-5" style={{ background: "rgba(0,0,0,0.15)" }}>
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-xs font-mono px-2 py-0.5 rounded"
                          style={{ background: "rgba(251,191,36,0.1)", color: "#fbbf24", border: "1px solid rgba(251,191,36,0.2)" }}>
                          {s.name}
                        </span>
                        <span className="text-xs" style={{ color: "rgba(250,248,242,0.4)" }}>{s.full}</span>
                        {s.violation && (
                          <span className="text-xs px-2 py-0.5 rounded-full ml-auto"
                            style={{ background: "rgba(248,113,113,0.1)", color: "#f87171", border: "1px solid rgba(248,113,113,0.2)" }}>
                            Potential violation
                          </span>
                        )}
                      </div>
                      <p className="text-xs leading-relaxed" style={{ color: "rgba(250,248,242,0.5)" }}>
                        {s.summary}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right — Scorecard */}
          <div className="flex flex-col gap-5">
            {/* Verdict */}
            <div className="rounded-2xl p-6 text-center"
              style={{
                background: "linear-gradient(135deg, rgba(52,211,153,0.1), rgba(99,71,212,0.1))",
                border: "1px solid rgba(52,211,153,0.3)",
              }}>
              <Gavel size={28} color="#34d399" className="mx-auto mb-3" />
              <div style={{ fontFamily: "var(--font-display)", fontSize: "3rem", lineHeight: 1, color: "#34d399" }}>
                {overallScore}
              </div>
              <div className="text-xs mt-1 mb-4" style={{ color: "rgba(250,248,242,0.4)" }}>out of 100</div>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium"
                style={{ background: "rgba(52,211,153,0.15)", color: "#34d399", border: "1px solid rgba(52,211,153,0.3)" }}>
                ✓ APPROVED FOR SUBMISSION
              </div>
            </div>

            {/* Score breakdown */}
            <div className="rounded-2xl p-6"
              style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.07)" }}>
              <p className="text-xs uppercase tracking-widest font-medium mb-5"
                style={{ color: "var(--purple-400)" }}>Judge scorecard</p>
              <div className="flex flex-col gap-4">
                {SCORES.map((score) => {
                  const display = score.invert
                    ? `${Math.round((1 - score.value) * 100)}%`
                    : `${Math.round(score.value * 100)}%`;
                  const barWidth = score.invert
                    ? `${Math.round((1 - score.value) * 100)}%`
                    : `${Math.round(score.value * 100)}%`;
                  return (
                    <div key={score.label}>
                      <div className="flex items-center justify-between text-xs mb-1.5">
                        <span style={{ color: "rgba(250,248,242,0.5)" }}>{score.label}</span>
                        <span style={{ color: score.color, fontWeight: 500 }}>{display}</span>
                      </div>
                      <div className="h-1.5 rounded-full" style={{ background: "rgba(255,255,255,0.06)" }}>
                        <div className="h-full rounded-full transition-all duration-1000"
                          style={{ width: barWidth, background: score.color }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Next steps */}
            <div className="rounded-2xl p-6"
              style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.07)" }}>
              <p className="text-xs uppercase tracking-widest font-medium mb-4"
                style={{ color: "var(--purple-400)" }}>Next steps</p>
              {[
                "Download your appeal packet PDF",
                "Sign the letter with your name and date",
                "Submit to your insurer's appeals department",
                "Follow up in 30 days if no response",
              ].map((step, i) => (
                <div key={i} className="flex items-start gap-3 mb-3 last:mb-0">
                  <div className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 text-xs font-medium"
                    style={{ background: "rgba(99,71,212,0.2)", color: "var(--purple-300)", border: "1px solid rgba(179,158,244,0.2)" }}>
                    {i + 1}
                  </div>
                  <p className="text-sm" style={{ color: "rgba(250,248,242,0.55)", lineHeight: 1.5 }}>{step}</p>
                </div>
              ))}
            </div>

            <Link href="/submit"
              className="btn-secondary flex items-center justify-center gap-2 px-5 py-3 rounded-full text-sm font-medium text-center"
              style={{ color: "rgba(250,248,242,0.5)" }}>
              Submit another case
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
