"use client";
import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { CheckCircle, Clock, AlertCircle, Scale } from "lucide-react";

type AgentStatus = "pending" | "running" | "done" | "error";

interface AgentState {
  id: string;
  name: string;
  role: string;
  color: string;
  bgColor: string;
  status: AgentStatus;
  elapsed: number | null;
  outputSnippet: string | null;
}

function makeAgents(): AgentState[] {
  return [
    { id: "auditor",    name: "Auditor",    role: "OCR & Parsing",   color: "#8b6fe8", bgColor: "rgba(139,111,232,0.1)", status: "pending", elapsed: null, outputSnippet: null },
    { id: "clinician",  name: "Clinician",  role: "PubMed Evidence", color: "#34d399", bgColor: "rgba(52,211,153,0.1)",  status: "pending", elapsed: null, outputSnippet: null },
    { id: "regulatory", name: "Regulatory", role: "Law & Statutes",  color: "#fbbf24", bgColor: "rgba(251,191,36,0.1)",  status: "pending", elapsed: null, outputSnippet: null },
    { id: "barrister",  name: "Barrister",  role: "Appeal Drafter",  color: "#60a5fa", bgColor: "rgba(96,165,250,0.1)",  status: "pending", elapsed: null, outputSnippet: null },
    { id: "judge",      name: "Judge",      role: "QA & Scoring",    color: "#f87171", bgColor: "rgba(248,113,113,0.1)", status: "pending", elapsed: null, outputSnippet: null },
  ];
}

function formatSnippet(agentId: string, output: Record<string, unknown>): string {
  try {
    if (agentId === "auditor")    return `${output.procedure_denied || "Procedure"} · Denial code: ${output.denial_code || "—"}`;
    if (agentId === "clinician")  return `${output.article_count || 0} PubMed articles retrieved`;
    if (agentId === "regulatory") return `${output.statute_count || 0} statutes identified · ${output.top_statute || ""}`;
    if (agentId === "barrister")  return String(output.preview || "Letter generated");
    if (agentId === "judge")      return `Score: ${output.score || 0} · ${output.recommendation || ""}`;
  } catch { /**/ }
  return JSON.stringify(output).slice(0, 80);
}



// ── Animated SVG icons per agent ─────────────────────────────────────────
function AgentIcon({ id, status, color }: { id: string; status: AgentStatus; color: string }) {
  const isRunning = status === "running";

  if (id === "auditor") return (
    <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
      <rect x="4" y="3" width="14" height="18" rx="2" stroke={color} strokeWidth="1.5" fill="none"/>
      <line x1="7" y1="8"  x2="15" y2="8"  stroke={color} strokeWidth="1.5" strokeLinecap="round">
        {isRunning && <animate attributeName="x2" values="7;15;7" dur="1.2s" repeatCount="indefinite"/>}
      </line>
      <line x1="7" y1="12" x2="15" y2="12" stroke={color} strokeWidth="1.5" strokeLinecap="round">
        {isRunning && <animate attributeName="x2" values="7;15;7" dur="1.2s" begin="0.2s" repeatCount="indefinite"/>}
      </line>
      <line x1="7" y1="16" x2="12" y2="16" stroke={color} strokeWidth="1.5" strokeLinecap="round">
        {isRunning && <animate attributeName="x2" values="7;12;7" dur="1.2s" begin="0.4s" repeatCount="indefinite"/>}
      </line>
      <circle cx="19" cy="19" r="4" stroke={color} strokeWidth="1.5" fill="none"/>
      <line x1="22" y1="22" x2="24" y2="24" stroke={color} strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );

  if (id === "clinician") return (
    <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
      <circle cx="13" cy="8" r="4" stroke={color} strokeWidth="1.5" fill="none"/>
      <path d="M5 22c0-4 3.6-7 8-7s8 3 8 7" stroke={color} strokeWidth="1.5" strokeLinecap="round" fill="none"/>
      <circle cx="20" cy="18" r="3" stroke={color} strokeWidth="1.5" fill="none">
        {isRunning && <animate attributeName="r" values="3;4;3" dur="1s" repeatCount="indefinite"/>}
      </circle>
      <line x1="20" y1="15.5" x2="20" y2="16.5" stroke={color} strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="20" y1="19.5" x2="20" y2="20.5" stroke={color} strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="17.5" y1="18" x2="18.5" y2="18" stroke={color} strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="21.5" y1="18" x2="22.5" y2="18" stroke={color} strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );

  if (id === "regulatory") return (
    <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
      <line x1="13" y1="3" x2="13" y2="6" stroke={color} strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="5"  y1="6" x2="21" y2="6" stroke={color} strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="13" y1="6" x2="5"  y2="6" stroke={color} strokeWidth="1" strokeLinecap="round"/>
      <line x1="13" y1="6" x2="21" y2="6" stroke={color} strokeWidth="1" strokeLinecap="round"/>
      <g>
        {isRunning && (
          <animateTransform attributeName="transform" type="rotate"
            values="-4 9 11;4 9 11;-4 9 11" dur="1.8s" repeatCount="indefinite"/>
        )}
        <line x1="5" y1="6" x2="5" y2="14" stroke={color} strokeWidth="1.5" strokeLinecap="round"/>
        <path d="M2 14 Q5 17 8 14" stroke={color} strokeWidth="1.5" fill="none" strokeLinecap="round"/>
      </g>
      <g>
        {isRunning && (
          <animateTransform attributeName="transform" type="rotate"
            values="4 17 11;-4 17 11;4 17 11" dur="1.8s" repeatCount="indefinite"/>
        )}
        <line x1="21" y1="6" x2="21" y2="14" stroke={color} strokeWidth="1.5" strokeLinecap="round"/>
        <path d="M18 14 Q21 17 24 14" stroke={color} strokeWidth="1.5" fill="none" strokeLinecap="round"/>
      </g>
      <line x1="10" y1="22" x2="16" y2="22" stroke={color} strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="13" y1="6"  x2="13" y2="22" stroke={color} strokeWidth="1" strokeLinecap="round"/>
    </svg>
  );

  if (id === "barrister") return (
    <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
      <rect x="4" y="4" width="15" height="18" rx="2" stroke={color} strokeWidth="1.5" fill="none"/>
      <line x1="7" y1="9"  x2="16" y2="9"  stroke={color} strokeWidth="1.2" strokeLinecap="round"/>
      <line x1="7" y1="13" x2="16" y2="13" stroke={color} strokeWidth="1.2" strokeLinecap="round"/>
      <line x1="7" y1="17" x2="13" y2="17" stroke={color} strokeWidth="1.2" strokeLinecap="round"/>
      <line x1="17" y1="17" x2="17" y2="22" stroke={color} strokeWidth="1.5" strokeLinecap="round">
        {isRunning && <animate attributeName="y2" values="17;22;17" dur="0.8s" repeatCount="indefinite"/>}
      </line>
      <circle cx="17" cy="16" r="1.5" fill={color}>
        {isRunning && <animate attributeName="opacity" values="1;0.3;1" dur="0.8s" repeatCount="indefinite"/>}
      </circle>
    </svg>
  );

  if (id === "judge") return (
    <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
      <rect x="8" y="4" width="10" height="7" rx="2" stroke={color} strokeWidth="1.5" fill="none"/>
      <line x1="13" y1="11" x2="13" y2="15" stroke={color} strokeWidth="1.5" strokeLinecap="round"/>
      <rect x="4" y="15" width="18" height="4" rx="1.5" stroke={color} strokeWidth="1.5" fill="none">
        {isRunning && (
          <animate attributeName="y" values="15;14;15" dur="0.5s" repeatCount="3"/>
        )}
      </rect>
      <line x1="6" y1="22" x2="20" y2="22" stroke={color} strokeWidth="2" strokeLinecap="round"/>
    </svg>
  );

  return null;
}

function AgentCard({ agent }: { agent: AgentState }) {
  const isRunning = agent.status === "running";

  return (
    <div style={{
      borderRadius: "1rem",
      padding: "1.25rem 1.5rem",
      transition: "all 0.5s ease",
      background: agent.status === "done"    ? `linear-gradient(135deg, ${agent.bgColor}, rgba(255,255,255,0.02))` :
                  isRunning                  ? "rgba(255,255,255,0.05)" : "rgba(255,255,255,0.02)",
      border: isRunning                  ? `1px solid ${agent.color}50` :
              agent.status === "done"    ? `1px solid ${agent.color}30` :
              agent.status === "error"   ? "1px solid rgba(248,113,113,0.3)" : "1px solid rgba(255,255,255,0.06)",
      boxShadow: isRunning ? `0 0 28px ${agent.color}18` : "none",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>

        {/* Animated icon */}
        <div style={{
          width: "3rem", height: "3rem", borderRadius: "0.875rem", flexShrink: 0,
          display: "flex", alignItems: "center", justifyContent: "center",
          background: agent.bgColor,
          boxShadow: isRunning ? `0 0 20px ${agent.color}50` : "none",
          transition: "box-shadow 0.4s ease",
        }}>
          <AgentIcon id={agent.id} status={agent.status} color={agent.color} />
        </div>

        {/* Body */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.5rem" }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem" }}>
              <span style={{ fontFamily: "var(--font-display)", fontSize: "1rem", color: "var(--cream)" }}>
                {agent.name}
              </span>
              <span style={{ fontSize: "0.72rem", color: "rgba(250,248,242,0.35)" }}>
                {agent.role}
              </span>
            </div>

            {/* Status badge */}
            <div style={{
              display: "flex", alignItems: "center", gap: "0.35rem",
              padding: "3px 10px", borderRadius: "9999px", fontSize: "0.7rem",
              fontWeight: 500, flexShrink: 0,
              background: agent.status === "done"    ? "rgba(52,211,153,0.12)" :
                          isRunning                  ? agent.bgColor :
                          agent.status === "error"   ? "rgba(248,113,113,0.12)" : "rgba(255,255,255,0.05)",
              color: agent.status === "done"  ? "#34d399" :
                     isRunning               ? agent.color :
                     agent.status === "error" ? "#f87171" : "rgba(250,248,242,0.3)",
            }}>
              {agent.status === "done"  && <CheckCircle size={10} />}
              {isRunning               && (
                <svg width="10" height="10" viewBox="0 0 10 10">
                  <circle cx="5" cy="5" r="4" stroke="currentColor" strokeWidth="1.5" fill="none" strokeDasharray="6 6">
                    <animateTransform attributeName="transform" type="rotate" from="0 5 5" to="360 5 5" dur="1s" repeatCount="indefinite"/>
                  </circle>
                </svg>
              )}
              {agent.status === "pending" && <Clock size={10} />}
              {agent.status === "error"   && <AlertCircle size={10} />}
              <span style={{ textTransform: "capitalize" }}>{agent.status}</span>
              {agent.elapsed !== null && (
                <span style={{ opacity: 0.6 }}> · {(agent.elapsed / 1000).toFixed(1)}s</span>
              )}
            </div>
          </div>

          {/* Output snippet */}
          {agent.outputSnippet && (
            <div style={{
              marginTop: "0.6rem", fontSize: "0.7rem", borderRadius: "0.5rem",
              padding: "0.4rem 0.75rem", fontFamily: "monospace",
              background: "rgba(0,0,0,0.3)", color: agent.color,
              border: `1px solid ${agent.color}20`, lineHeight: 1.6,
            }}>
              {agent.outputSnippet}
            </div>
          )}

          {/* Running progress bar */}
          {isRunning && (
            <div style={{ marginTop: "0.6rem", height: "3px", borderRadius: "9999px", overflow: "hidden", background: "rgba(255,255,255,0.06)" }}>
              <div style={{
                height: "100%", borderRadius: "9999px", width: "40%",
                background: `linear-gradient(90deg, transparent, ${agent.color}, transparent)`,
                animation: "shimmer 1.5s infinite",
              }} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function CasePage() {
  const params  = useParams();
  const router  = useRouter();
  const sessionId = params.id as string;
  const [agents, setAgents] = useState<AgentState[]>(makeAgents());
  const [done,   setDone]   = useState(false);

  const completedCount = agents.filter(a => a.status === "done").length;
  const progress = Math.round((completedCount / agents.length) * 100);

  const updateAgent = (id: string, patch: Partial<AgentState>) =>
    setAgents(prev => prev.map(a => a.id === id ? { ...a, ...patch } : a));

  useEffect(() => {
    if (!sessionId) return;

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const es = new EventSource(`${apiUrl}/api/case/${sessionId}/stream`);
    let connected = false;

    es.onopen = () => { connected = true; };

    es.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data);
        if (event.type === "agent_start") updateAgent(event.agent, { status: "running" });
        if (event.type === "agent_done")  updateAgent(event.agent, { status: "done", elapsed: event.elapsed_ms, outputSnippet: formatSnippet(event.agent, event.output || {}) });
        if (event.type === "agent_error") updateAgent(event.agent, { status: "error" });
        if (event.type === "pipeline_done" || event.type === "close") { setDone(true); es.close(); }
      } catch { /**/ }
    };

    es.onerror = () => { es.close(); };
    return () => es.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);



  return (
    <div style={{ minHeight: "100vh", background: "var(--purple-950)", position: "relative" }}>
      <style>{`
        @keyframes shimmer { 0%{transform:translateX(-200%)} 100%{transform:translateX(400%)} }
      `}</style>
      <div className="orb orb-1" style={{ position: "fixed", opacity: 0.4 }} />

      {/* Header */}
      <header style={{ position: "relative", zIndex: 10, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1.25rem 2rem", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <Link href="/" style={{ display: "flex", alignItems: "center", gap: "0.5rem", textDecoration: "none" }}>
          <div style={{ width: "1.75rem", height: "1.75rem", borderRadius: "0.5rem", display: "flex", alignItems: "center", justifyContent: "center", background: "linear-gradient(135deg, #4f31b8, #8b6fe8)" }}>
            <Scale size={14} color="white" />
          </div>
          <span style={{ fontFamily: "var(--font-display)", fontSize: "1.1rem", color: "var(--cream)" }}>
            Advoc<span className="gold-text">AI</span>
          </span>
        </Link>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>

          <span style={{ fontSize: "0.7rem", fontFamily: "monospace", color: "rgba(250,248,242,0.2)" }}>{sessionId}</span>
        </div>
      </header>

      <main style={{ position: "relative", zIndex: 10, maxWidth: "640px", margin: "0 auto", padding: "3rem 1.5rem" }}>
        {/* Title */}
        <div style={{ textAlign: "center", marginBottom: "2.5rem" }}>
          <h1 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(1.8rem,5vw,2.8rem)", lineHeight: 1.1, marginBottom: "0.625rem" }}>
            {done ? <span className="gradient-text">Appeal ready.</span> : <>Agents at work<span className="cursor"/></>}
          </h1>
          <p style={{ fontSize: "0.9rem", color: "rgba(250,248,242,0.4)" }}>
            {done ? "Your complete appeal packet has been generated." : "Five AI specialists are building your appeal in real time."}
          </p>
        </div>

        {/* Progress bar */}
        <div style={{ height: "6px", borderRadius: "9999px", marginBottom: "0.75rem", overflow: "hidden", background: "rgba(255,255,255,0.06)" }}>
          <div style={{ height: "100%", borderRadius: "9999px", transition: "width 0.7s ease", width: `${progress}%`, background: done ? "linear-gradient(90deg,#34d399,#6347d4)" : "linear-gradient(90deg,#6347d4,#8b6fe8)" }} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "rgba(250,248,242,0.3)", marginBottom: "2rem" }}>
          <span>{completedCount} of 5 agents complete</span>
          <span>{progress}%</span>
        </div>

        {/* Agent cards */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.875rem" }}>
          {agents.map(agent => <AgentCard key={agent.id} agent={agent} />)}
        </div>

        {/* Done CTA */}
        {done && (
          <div style={{ marginTop: "2.5rem", borderRadius: "1.5rem", padding: "2rem", textAlign: "center", background: "linear-gradient(135deg,rgba(79,49,184,0.2),rgba(52,211,153,0.08))", border: "1px solid rgba(52,211,153,0.25)" }}>
            <div style={{ width: "3.5rem", height: "3.5rem", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 1.25rem", background: "rgba(52,211,153,0.12)" }}>
              <CheckCircle size={26} color="#34d399" />
            </div>
            <h2 style={{ fontFamily: "var(--font-display)", fontSize: "1.5rem", marginBottom: "0.5rem" }}>Your appeal is ready</h2>
            <p style={{ fontSize: "0.875rem", marginBottom: "2rem", color: "rgba(250,248,242,0.5)" }}>
              The Judge has scored and validated your appeal.
            </p>
            <button onClick={() => router.push(`/case/${sessionId}/letter`)} className="btn-primary"
              style={{ display: "inline-flex", alignItems: "center", gap: "0.75rem", padding: "0.875rem 2rem", borderRadius: "9999px", fontSize: "0.9rem", fontWeight: 500, color: "white", cursor: "pointer" }}>
              <span>View your appeal letter</span>
              <span style={{ color: "var(--gold-light)" }}>→</span>
            </button>
          </div>
        )}
      </main>
    </div>
  );
}