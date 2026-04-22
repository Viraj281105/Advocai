"use client";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  Scale, Copy, Check, Download, ChevronDown, ChevronUp,
  BookOpen, Gavel, ExternalLink
} from "lucide-react";

export default function LetterPage() {
  const params = useParams();
  const sessionId = params.id as string;
  const [copied, setCopied] = useState(false);
  const [evidenceOpen, setEvidenceOpen] = useState(true);
  const [statutesOpen, setStatutesOpen] = useState(true);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!sessionId) return;
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${apiUrl}/api/case/${sessionId}/result`)
      .then(res => res.json())
      .then(data => {
        setResult(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [sessionId]);

  const letterText = result?.barrister || "Appeal letter is not available.";
  const pubmedEvidence = result?.clinician?.root || result?.clinician?.articles || [];
  const statutes = result?.regulatory?.legal_points || [];
  const overallScore = result?.judge?.overall_score || 0;
  const subScores = result?.judge?.sub_scores || {};

  const scoresList = [
    { label: "Clinical alignment", value: subScores.clinical_alignment ?? 0, color: "#34d399" },
    { label: "Legal compliance", value: subScores.legal_compliance ?? 0, color: "#60a5fa" },
    { label: "Structure integrity", value: subScores.structure_integrity ?? 0, color: "#8b6fe8" },
    { label: "Hallucination score", value: subScores.hallucination_score ?? 0, color: "#fbbf24", invert: true },
  ];

  const copyLetter = () => {
    navigator.clipboard.writeText(letterText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadUrl = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/case/${sessionId}/download`;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--purple-950)" }}>
        <p style={{ color: "var(--cream)" }}>Loading appeal packet...</p>
      </div>
    );
  }

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
          <span style={{ fontFamily: "var(--font-display)", fontSize: "1.1rem", color: "var(--cream)" }}>
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
          <a
            href={downloadUrl}
            target="_blank" rel="noreferrer"
            className="btn-primary flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium text-white cursor-pointer decoration-none"
            style={{ textDecoration: "none" }}
          >
            <Download size={13} />
            <span>Download packet</span>
          </a>
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
              {letterText}
            </div>
          </div>

            {/* Evidence explorer */}
            {pubmedEvidence.length > 0 && (
              <div className="rounded-2xl overflow-hidden"
                style={{ border: "1px solid rgba(255,255,255,0.07)" }}>
                <button
                  onClick={() => setEvidenceOpen((o) => !o)}
                  className="w-full flex items-center justify-between px-6 py-4 cursor-pointer transition-colors border-none"
                  style={{ background: "rgba(255,255,255,0.03)" }}
                >
                  <div className="flex items-center gap-3">
                    <BookOpen size={16} color="#34d399" />
                    <span className="text-sm font-medium" style={{ color: "var(--cream)" }}>
                      PubMed evidence ({pubmedEvidence.length} articles)
                    </span>
                  </div>
                  {evidenceOpen ? <ChevronUp size={16} color="rgba(250,248,242,0.4)" /> : <ChevronDown size={16} color="rgba(250,248,242,0.4)" />}
                </button>
                {evidenceOpen && (
                  <div className="divide-y" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
                    {pubmedEvidence.map((art: any, i: number) => (
                      <div key={art.pubmed_id || i} className="px-6 py-5" style={{ background: "rgba(0,0,0,0.15)" }}>
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <p className="text-sm font-medium" style={{ color: "var(--cream)" }}>
                            {art.article_title || "Untitled"}
                          </p>
                          {art.pubmed_id && (
                            <a
                              href={`https://pubmed.ncbi.nlm.nih.gov/${art.pubmed_id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex-shrink-0"
                            >
                              <ExternalLink size={13} color="rgba(250,248,242,0.3)" />
                            </a>
                          )}
                        </div>
                        {art.pubmed_id && (
                          <p className="text-xs mb-2" style={{ color: "rgba(250,248,242,0.4)" }}>
                            PMID: {art.pubmed_id}
                          </p>
                        )}
                        <p className="text-xs leading-relaxed" style={{ color: "rgba(250,248,242,0.5)" }}>
                          {art.summary_of_finding || art.summary || ""}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Statutes */}
            {statutes.length > 0 && (
              <div className="rounded-2xl overflow-hidden"
                style={{ border: "1px solid rgba(255,255,255,0.07)" }}>
                <button
                  onClick={() => setStatutesOpen((o) => !o)}
                  className="w-full flex items-center justify-between px-6 py-4 cursor-pointer border-none"
                  style={{ background: "rgba(255,255,255,0.03)" }}
                >
                  <div className="flex items-center gap-3">
                    <Scale size={16} color="#fbbf24" />
                    <span className="text-sm font-medium" style={{ color: "var(--cream)" }}>
                      Legal statutes cited ({statutes.length})
                    </span>
                  </div>
                  {statutesOpen ? <ChevronUp size={16} color="rgba(250,248,242,0.4)" /> : <ChevronDown size={16} color="rgba(250,248,242,0.4)" />}
                </button>
                {statutesOpen && (
                  <div className="divide-y" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
                    {statutes.map((s: any, i: number) => (
                      <div key={s.statute || i} className="px-6 py-5" style={{ background: "rgba(0,0,0,0.15)" }}>
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-xs font-mono px-2 py-0.5 rounded"
                            style={{ background: "rgba(251,191,36,0.1)", color: "#fbbf24", border: "1px solid rgba(251,191,36,0.2)" }}>
                            {s.statute}
                          </span>
                        </div>
                        <p className="text-xs leading-relaxed" style={{ color: "rgba(250,248,242,0.5)" }}>
                          {s.summary}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
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
                {scoresList.map((score) => {
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
              className="btn-secondary flex items-center justify-center gap-2 px-5 py-3 rounded-full text-sm font-medium text-center decoration-none"
              style={{ color: "rgba(250,248,242,0.5)", textDecoration: "none" }}>
              Submit another case
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
