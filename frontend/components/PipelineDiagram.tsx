"use client";

import { useState } from "react";

// ─── Agent data ───────────────────────────────────────────────────────────────

type AgentId = "auditor" | "clinician" | "regulatory" | "barrister" | "judge";

interface AgentMeta {
  emoji: string;
  title: string;
  file: string;
  time: string;
  desc: string;
  outputs: string[];
  accent: string;       // fill colour
  border: string;       // stroke colour
  textColor: string;    // label colour
  step: string;
}

const AGENTS: Record<AgentId, AgentMeta> = {
  auditor: {
    emoji: "🔍",
    title: "Auditor — OCR & Parsing",
    file: "agents/auditor.py",
    time: "~2.1s",
    desc: "Extracts ICD/CPT codes, denial reason, and insurer policy clause from both uploaded PDFs using Gemini vision. Outputs a typed StructuredDenial Pydantic object.",
    outputs: ["StructuredDenial", "ICD / CPT codes", "Policy clause"],
    accent: "#EEEDFE",
    border: "#534AB7",
    textColor: "#3C3489",
    step: "01",
  },
  clinician: {
    emoji: "🩺",
    title: "Clinician — PubMed Evidence",
    file: "agents/clinician.py",
    time: "~6–10s",
    desc: "Generates targeted PubMed queries from the denial context, retrieves peer-reviewed studies via the PubMed API, and ranks by clinical relevance. Returns an EvidenceList with PMIDs.",
    outputs: ["EvidenceList", "PubMed IDs", "Summaries"],
    accent: "#E1F5EE",
    border: "#0F6E56",
    textColor: "#085041",
    step: "02",
  },
  regulatory: {
    emoji: "⚖️",
    title: "Regulatory — Statute Matching",
    file: "agents/regulatory.py",
    time: "~3s",
    desc: "Matches the denial against ACA §2713, ERISA, state insurance mandates, and other statutes. Keyword matching today — semantic pgvector search planned in Issue #13.",
    outputs: ["Legal points", "Statute refs", "ACA / ERISA"],
    accent: "#FAEEDA",
    border: "#BA7517",
    textColor: "#633806",
    step: "03",
  },
  barrister: {
    emoji: "📜",
    title: "Barrister — Appeal Letter",
    file: "agents/barrister.py",
    time: "~2–4s",
    desc: "Composes a polished appellate letter integrating clinical evidence, statutory arguments, and policy-language conflicts. Maintains professional legal tone with structured section formatting.",
    outputs: ["Appeal letter", "Full text", "Structured"],
    accent: "#FAECE7",
    border: "#993C1D",
    textColor: "#4A1B0C",
    step: "04",
  },
  judge: {
    emoji: "🏛️",
    title: "Judge — QA Scorecard",
    file: "agents/judge.py",
    time: "~1–2s",
    desc: "Independently evaluates the appeal for citation accuracy, legal compliance, clinical alignment, structure integrity, and hallucination risk. Returns a 0–100 score and APPROVE / REVISE recommendation.",
    outputs: ["Judge score", "0–100 rating", "APPROVE / REVISE"],
    accent: "#E6F1FB",
    border: "#185FA5",
    textColor: "#042C53",
    step: "05",
  },
};

const AGENT_ORDER: AgentId[] = ["auditor", "clinician", "regulatory", "barrister"];

// ─── Node component ───────────────────────────────────────────────────────────

function AgentNode({
  id,
  cx,
  cy,
  active,
  onClick,
}: {
  id: AgentId;
  cx: number;
  cy: number;
  active: boolean;
  onClick: () => void;
}) {
  const [hovered, setHovered] = useState(false);
  const a = AGENTS[id];
  const scale = hovered || active ? 1.06 : 1;

  return (
    <g
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{ cursor: "pointer", transform: `scale(${scale})`, transformOrigin: `${cx}px ${cy}px`, transition: "transform 0.15s ease" }}
    >
      {/* Outer ring — glows when active */}
      <circle
        cx={cx}
        cy={cy}
        r={46}
        fill="none"
        stroke={a.border}
        strokeWidth={active ? 2 : 1}
        strokeOpacity={active ? 0.7 : 0.25}
      />
      {/* Fill circle */}
      <circle cx={cx} cy={cy} r={38} fill={a.accent} stroke={a.border} strokeWidth={1} />
      {/* Step label above */}
      <text
        x={cx}
        y={cy - 54}
        textAnchor="middle"
        fontSize={10}
        fontWeight={500}
        fill={a.border}
        fillOpacity={0.6}
        fontFamily="'DM Sans', sans-serif"
      >
        {a.step}
      </text>
      {/* Emoji */}
      <text x={cx} y={cy + 6} textAnchor="middle" fontSize={20} dominantBaseline="middle">
        {a.emoji}
      </text>
      {/* Name */}
      <text
        x={cx}
        y={cy + 26}
        textAnchor="middle"
        fontSize={11}
        fontWeight={500}
        fill={a.textColor}
        fontFamily="'DM Sans', sans-serif"
      >
        {id.charAt(0).toUpperCase() + id.slice(1)}
      </text>
    </g>
  );
}

// ─── Animated flow line ───────────────────────────────────────────────────────

function FlowLine({ x1, y1, x2, y2, delay = 0 }: { x1: number; y1: number; x2: number; y2: number; delay?: number }) {
  return (
    <>
      <line
        x1={x1} y1={y1} x2={x2} y2={y2}
        stroke="#7F77DD"
        strokeWidth={2}
        strokeDasharray="8 4"
        style={{ animation: `flowPulse 2s linear infinite`, animationDelay: `${delay}s` }}
      />
      {/* Static arrowhead */}
      <line x1={x2 - 6} y1={y1} x2={x2} y2={y2} stroke="#7F77DD" strokeWidth={2} markerEnd="url(#arr)" />
    </>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function PipelineDiagram() {
  const [active, setActive] = useState<AgentId | null>(null);

  function toggle(id: AgentId) {
    setActive(prev => (prev === id ? null : id));
  }

  const detail = active ? AGENTS[active] : null;

  // Node X positions for the horizontal row
  const nodeY = 110;
  const nodeXs: Record<AgentId, number> = {
    auditor:    142,
    clinician:  262,
    regulatory: 382,
    barrister:  502,
    judge:      382, // centred below Regulatory
  };

  return (
    <section
      style={{
        padding: "80px 32px",
        maxWidth: "960px",
        margin: "0 auto",
        fontFamily: "'DM Sans', sans-serif",
      }}
    >
      {/* Heading */}
      <div style={{ textAlign: "center", marginBottom: "48px" }}>
        <p
          style={{
            fontSize: "0.75rem",
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            color: "rgba(250,248,242,0.4)",
            margin: "0 0 12px",
          }}
        >
          System Architecture
        </p>
        <h2
          style={{
            fontFamily: "'DM Serif Display', serif",
            fontSize: "clamp(1.6rem, 3vw, 2.2rem)",
            fontWeight: 400,
            color: "#faf8f2",
            margin: 0,
            letterSpacing: "-0.5px",
          }}
        >
          Five agents. One appeal.
        </h2>
        <p style={{ color: "rgba(250,248,242,0.45)", fontSize: "0.9375rem", marginTop: "12px" }}>
          Click any agent to see what it does.
        </p>
      </div>

      {/* SVG Diagram */}
      <div
        style={{
          background: "rgba(255,255,255,0.03)",
          border: "1px solid rgba(255,255,255,0.07)",
          borderRadius: "20px",
          padding: "24px 16px 12px",
          overflow: "hidden",
        }}
      >
        <svg width="100%" viewBox="0 0 680 270" style={{ overflow: "visible" }}>
          <defs>
            <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
            </marker>
          </defs>

          <style>{`
            @keyframes flowPulse {
              0%   { stroke-dashoffset: 60; opacity: 0.25; }
              50%  { opacity: 0.9; }
              100% { stroke-dashoffset: 0;  opacity: 0.25; }
            }
          `}</style>

          {/* Input label */}
          <text x={30} y={106} fontSize={10} fill="rgba(250,248,242,0.35)" fontFamily="'DM Sans',sans-serif">Denial</text>
          <text x={30} y={119} fontSize={10} fill="rgba(250,248,242,0.35)" fontFamily="'DM Sans',sans-serif">PDF</text>
          <line x1={62} y1={nodeY} x2={96} y2={nodeY} stroke="#7F77DD" strokeWidth={1.5} markerEnd="url(#arr)" fill="none" />

          {/* Horizontal flow lines between top-row agents */}
          <FlowLine x1={nodeXs.auditor + 40}    y1={nodeY} x2={nodeXs.clinician - 40}   y2={nodeY} delay={0}   />
          <FlowLine x1={nodeXs.clinician + 40}  y1={nodeY} x2={nodeXs.regulatory - 40}  y2={nodeY} delay={0.5} />
          <FlowLine x1={nodeXs.regulatory + 40} y1={nodeY} x2={nodeXs.barrister - 40}   y2={nodeY} delay={1.0} />

          {/* Top-row agents */}
          {AGENT_ORDER.map((id) => (
            <AgentNode
              key={id}
              id={id}
              cx={nodeXs[id]}
              cy={nodeY}
              active={active === id}
              onClick={() => toggle(id)}
            />
          ))}

          {/* Down from Barrister → Judge row */}
          <line
            x1={nodeXs.barrister} y1={nodeY + 40} x2={nodeXs.barrister} y2={185}
            stroke="#7F77DD" strokeWidth={1.5} strokeDasharray="6 4"
            style={{ animation: "flowPulse 2s linear infinite", animationDelay: "1.5s" }}
          />
          <line x1={nodeXs.barrister} y1={182} x2={nodeXs.barrister} y2={188} stroke="#7F77DD" strokeWidth={2} markerEnd="url(#arr)" fill="none"/>

          {/* Horizontal to Judge */}
          <line x1={nodeXs.barrister} y1={190} x2={nodeXs.judge + 42} y2={190}
            stroke="#7F77DD" strokeWidth={1.5} strokeDasharray="5 3" opacity={0.5} fill="none" />
          <line x1={nodeXs.judge + 44} y1={190} x2={nodeXs.judge + 40} y2={190}
            stroke="#7F77DD" strokeWidth={2} markerEnd="url(#arr)" fill="none"/>

          {/* Judge node (shifted down) */}
          <AgentNode
            id="judge"
            cx={nodeXs.judge}
            cy={nodeY + 80}
            active={active === "judge"}
            onClick={() => toggle("judge")}
          />

          {/* Output from Judge */}
          <line x1={nodeXs.judge + 40} y1={nodeY + 80} x2={620} y2={nodeY + 80}
            stroke="#7F77DD" strokeWidth={1.5} strokeDasharray="5 3" opacity={0.5} fill="none"/>
          <line x1={618} y1={nodeY + 80} x2={624} y2={nodeY + 80} stroke="#7F77DD" strokeWidth={2} markerEnd="url(#arr)" fill="none"/>
          <text x={630} y={nodeY + 76} fontSize={10} fill="rgba(250,248,242,0.35)" fontFamily="'DM Sans',sans-serif">Appeal</text>
          <text x={630} y={nodeY + 89} fontSize={10} fill="rgba(250,248,242,0.35)" fontFamily="'DM Sans',sans-serif">PDF</text>
        </svg>

        {/* Detail panel */}
        {detail && (
          <div
            style={{
              margin: "8px 8px 8px",
              padding: "16px 20px",
              background: "rgba(255,255,255,0.04)",
              border: `1px solid ${detail.border}40`,
              borderRadius: "14px",
              animation: "fadeIn 0.2s ease",
            }}
          >
            <style>{`@keyframes fadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }`}</style>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "10px" }}>
              <div>
                <p style={{ margin: 0, fontWeight: 600, fontSize: "0.9375rem", color: "#faf8f2" }}>{detail.title}</p>
                <p style={{ margin: "2px 0 0", fontSize: "0.75rem", color: "rgba(250,248,242,0.35)", fontFamily: "monospace" }}>{detail.file}</p>
              </div>
              <span style={{ fontSize: "0.75rem", color: "rgba(250,248,242,0.3)", whiteSpace: "nowrap", marginLeft: "16px" }}>
                avg {detail.time}
              </span>
            </div>
            <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginBottom: "12px" }}>
              {detail.outputs.map((o) => (
                <span
                  key={o}
                  style={{
                    fontSize: "0.7rem",
                    fontWeight: 500,
                    padding: "3px 10px",
                    borderRadius: "999px",
                    background: `${detail.border}18`,
                    color: detail.border,
                    border: `1px solid ${detail.border}40`,
                  }}
                >
                  {o}
                </span>
              ))}
            </div>
            <p style={{ margin: 0, fontSize: "0.8125rem", color: "rgba(250,248,242,0.5)", lineHeight: 1.6 }}>{detail.desc}</p>
          </div>
        )}
      </div>
    </section>
  );
}
