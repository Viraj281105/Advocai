"use client";
import { Search, Stethoscope, Scale, PenLine, Gavel } from "lucide-react";

const AGENTS = [
  { id: "auditor",    number: "01", name: "Auditor",    role: "OCR & Parsing",    description: "Scans your denial letter and policy PDF. Extracts ICD/CPT codes, identifies the denial reason, and maps the relevant policy clause.", icon: Search,      color: "#8b6fe8", bgColor: "rgba(139,111,232,0.1)", output: '{ "denial_code": "CO-50", "procedure": "Genomic Sequencing" }' },
  { id: "clinician",  number: "02", name: "Clinician",  role: "PubMed Evidence",  description: "Queries PubMed with AI-generated search terms. Retrieves peer-reviewed studies proving your treatment is medically necessary.",            icon: Stethoscope, color: "#34d399", bgColor: "rgba(52,211,153,0.1)",   output: '{ "articles": 7, "top_pmid": "38291045" }' },
  { id: "regulatory", number: "03", name: "Regulatory", role: "Law & Statute",    description: "Identifies ACA, ERISA, and state-level statutes that mandate your coverage. Flags policy-language conflicts with the law.",                icon: Scale,       color: "#fbbf24", bgColor: "rgba(251,191,36,0.1)",  output: '{ "statute": "ACA §2713", "violation": true }' },
  { id: "barrister",  number: "04", name: "Barrister",  role: "Appeal Drafter",   description: "Weaves the medical evidence and legal arguments into a structured, professional appellate letter with legal-grade tone.",                    icon: PenLine,     color: "#60a5fa", bgColor: "rgba(96,165,250,0.1)",  output: '"Dear Appeals Board, This letter constitutes..."' },
  { id: "judge",      number: "05", name: "Judge",      role: "QA & Scoring",     description: "Evaluates the letter for clinical accuracy, legal compliance, structural integrity, and hallucination detection. Scores and approves.",       icon: Gavel,       color: "#f87171", bgColor: "rgba(248,113,113,0.1)", output: '{ "score": 0.91, "recommendation": "APPROVE" }' },
];

export default function AgentCards() {
  return (
    <section id="agents" style={{ position: "relative", padding: "6rem 1.5rem" }}>
      <div style={{ maxWidth: "1280px", margin: "0 auto" }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "5rem" }}>
          <p style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.15em", color: "var(--purple-400)", fontWeight: 500, marginBottom: "1rem" }}>
            The pipeline
          </p>
          <h2 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(2rem, 5vw, 3.5rem)", lineHeight: 1.1, letterSpacing: "-0.02em" }}>
            Five agents.{" "}
            <span className="gradient-text">One airtight appeal.</span>
          </h2>
          <p style={{ marginTop: "1.5rem", fontSize: "1.1rem", color: "rgba(250,248,242,0.5)", lineHeight: 1.7, maxWidth: "600px", margin: "1.5rem auto 0" }}>
            Each agent is a specialist. Together they form a complete legal and medical team — deployed automatically the moment you upload your denial.
          </p>
        </div>

        {/* Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 300px), 1fr))", gap: "1rem", }}>
          {AGENTS.map((agent) => {
            const Icon = agent.icon;
            return (
              <div
                key={agent.id}
                className={`agent-card agent-card-${agent.id}`}
                style={{
                  background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(255,255,255,0.07)",
                  borderRadius: "1rem",
                  padding: "1.75rem",
                  display: "flex",
                  flexDirection: "column",
                  gap: "1.25rem",
                  transition: "background 0.3s ease, border-color 0.3s ease, transform 0.3s ease",
                  cursor: "default",
                  backdropFilter: "blur(12px)",
                }}
                onMouseEnter={e => {
                  (e.currentTarget as HTMLDivElement).style.background = "rgba(255,255,255,0.06)";
                  (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(179,158,244,0.25)";
                  (e.currentTarget as HTMLDivElement).style.transform = "translateY(-2px)";
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLDivElement).style.background = "rgba(255,255,255,0.03)";
                  (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(255,255,255,0.07)";
                  (e.currentTarget as HTMLDivElement).style.transform = "translateY(0)";
                }}
              >
                {/* Top row */}
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
                  <div
                    className="agent-icon-wrap"
                    style={{ width: "3rem", height: "3rem", borderRadius: "0.75rem", display: "flex", alignItems: "center", justifyContent: "center", background: agent.bgColor, transition: "box-shadow 0.3s ease" }}
                  >
                    <Icon size={22} color={agent.color} />
                  </div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 500, color: agent.color, background: agent.bgColor, padding: "4px 10px", borderRadius: "20px" }}>
                    {agent.role}
                  </span>
                </div>

                {/* Name + description */}
                <div>
                  <div style={{ display: "flex", alignItems: "baseline", gap: "0.75rem" }}>
                    <span style={{ fontSize: "0.75rem", fontWeight: 500, color: "rgba(250,248,242,0.25)" }}>{agent.number}</span>
                    <h3 style={{ fontFamily: "var(--font-display)", fontSize: "1.4rem", color: "var(--cream)" }}>{agent.name}</h3>
                  </div>
                  <p style={{ marginTop: "0.75rem", fontSize: "0.875rem", lineHeight: 1.6, color: "rgba(250,248,242,0.5)" }}>
                    {agent.description}
                  </p>
                </div>

                {/* Output */}
                <div style={{ marginTop: "auto", background: "rgba(0,0,0,0.3)", border: `1px solid ${agent.color}22`, borderRadius: "0.5rem", padding: "0.75rem", fontSize: "0.75rem", fontFamily: "monospace", color: agent.color, lineHeight: 1.6, wordBreak: "break-all" }}>
                  {agent.output}
                </div>
              </div>
            );
          })}

          {/* Final output card */}
          <div style={{ background: "linear-gradient(135deg, rgba(79,49,184,0.2), rgba(99,71,212,0.1))", border: "1px solid rgba(179,158,244,0.2)", borderRadius: "1rem", padding: "1.75rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
            <p style={{ fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.12em", color: "var(--purple-400)", fontWeight: 500 }}>Final output</p>
            <h3 style={{ fontFamily: "var(--font-display)", fontSize: "1.4rem" }}>Complete appeal packet</h3>
            <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "0.75rem", marginTop: "0.5rem" }}>
              {["Structured appeal letter (PDF)", "PubMed evidence dossier", "Legal statute brief", "Judge QA scorecard", "Full JSON audit trail"].map(item => (
                <li key={item} style={{ display: "flex", alignItems: "center", gap: "0.75rem", fontSize: "0.875rem", color: "rgba(250,248,242,0.6)" }}>
                  <span style={{ color: "var(--gold-light)" }}>✓</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
