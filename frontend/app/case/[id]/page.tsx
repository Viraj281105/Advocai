"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Search, Stethoscope, Scale, PenLine, Gavel,
  CheckCircle, Loader2, Clock, AlertCircle, Scale as ScaleIcon
} from "lucide-react";

type AgentStatus = "pending" | "running" | "done" | "error";

interface AgentState {
  id: string;
  name: string;
  role: string;
  color: string;
  bgColor: string;
  icon: React.ReactNode;
  status: AgentStatus;
  elapsed: number | null;
  outputSnippet: string | null;
}

const MOCK_OUTPUTS: Record<string, string> = {
  auditor: 'Denial code: CO-50 · Procedure: Genomic Sequencing · Policy clause detected',
  clinician: '7 PubMed articles retrieved · Top study: PMID 38291045',
  regulatory: 'ACA §2713 violation identified · ERISA §502(a) applicable',
  barrister: '"Dear Appeals Board, This letter constitutes a formal appeal..."',
  judge: 'Score: 0.91 · Legal compliance: 0.88 · Recommendation: APPROVE ✓',
};

function makeAgents(): AgentState[] {
  return [
    { id: "auditor",    name: "Auditor",    role: "OCR & Parsing",     color: "#8b6fe8", bgColor: "rgba(139,111,232,0.1)", icon: <Search size={20} />,       status: "pending", elapsed: null, outputSnippet: null },
    { id: "clinician",  name: "Clinician",  role: "PubMed Evidence",   color: "#34d399", bgColor: "rgba(52,211,153,0.1)",  icon: <Stethoscope size={20} />,   status: "pending", elapsed: null, outputSnippet: null },
    { id: "regulatory", name: "Regulatory", role: "Law & Statutes",    color: "#fbbf24", bgColor: "rgba(251,191,36,0.1)",  icon: <Scale size={20} />,         status: "pending", elapsed: null, outputSnippet: null },
    { id: "barrister",  name: "Barrister",  role: "Appeal Drafter",    color: "#60a5fa", bgColor: "rgba(96,165,250,0.1)",  icon: <PenLine size={20} />,       status: "pending", elapsed: null, outputSnippet: null },
    { id: "judge",      name: "Judge",      role: "QA & Scoring",      color: "#f87171", bgColor: "rgba(248,113,113,0.1)", icon: <Gavel size={20} />,         status: "pending", elapsed: null, outputSnippet: null },
  ];
}

function AgentCard({ agent, isActive }: { agent: AgentState; isActive: boolean }) {
  return (
    <div
      className="rounded-2xl p-6 transition-all duration-500"
      style={{
        background:
          agent.status === "done"
            ? `linear-gradient(135deg, ${agent.bgColor}, rgba(255,255,255,0.02))`
            : agent.status === "running"
            ? "rgba(255,255,255,0.05)"
            : "rgba(255,255,255,0.02)",
        border:
          agent.status === "running"
            ? `1px solid ${agent.color}50`
            : agent.status === "done"
            ? `1px solid ${agent.color}30`
            : "1px solid rgba(255,255,255,0.06)",
        boxShadow: agent.status === "running" ? `0 0 24px ${agent.color}15` : "none",
      }}
    >
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div
          className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 transition-all duration-300"
          style={{
            background: agent.bgColor,
            color: agent.color,
            boxShadow: agent.status === "running" ? `0 0 16px ${agent.color}40` : "none",
          }}
        >
          {agent.status === "running" ? (
            <Loader2 size={20} color={agent.color} className="animate-spin" />
          ) : (
            <span style={{ color: agent.color }}>{agent.icon}</span>
          )}
        </div>

        {/* Body */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-3 mb-1">
            <div>
              <span
                className="font-medium text-sm"
                style={{ color: "var(--cream)", fontFamily: "var(--font-display)", fontSize: "1rem" }}
              >
                {agent.name}
              </span>
              <span
                className="text-xs ml-2"
                style={{ color: "rgba(250,248,242,0.35)" }}
              >
                {agent.role}
              </span>
            </div>

            {/* Status badge */}
            <div
              className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium flex-shrink-0"
              style={{
                background:
                  agent.status === "done"
                    ? "rgba(52,211,153,0.12)"
                    : agent.status === "running"
                    ? `${agent.bgColor}`
                    : agent.status === "error"
                    ? "rgba(248,113,113,0.12)"
                    : "rgba(255,255,255,0.05)",
                color:
                  agent.status === "done"
                    ? "#34d399"
                    : agent.status === "running"
                    ? agent.color
                    : agent.status === "error"
                    ? "#f87171"
                    : "rgba(250,248,242,0.3)",
              }}
            >
              {agent.status === "done" && <CheckCircle size={11} />}
              {agent.status === "running" && <Loader2 size={11} className="animate-spin" />}
              {agent.status === "pending" && <Clock size={11} />}
              {agent.status === "error" && <AlertCircle size={11} />}
              <span className="capitalize">{agent.status}</span>
              {agent.elapsed !== null && (
                <span style={{ opacity: 0.6 }}> · {(agent.elapsed / 1000).toFixed(1)}s</span>
              )}
            </div>
          </div>

          {/* Output snippet */}
          {agent.outputSnippet && (
            <div
              className="mt-3 text-xs rounded-lg px-3 py-2 font-mono"
              style={{
                background: "rgba(0,0,0,0.3)",
                color: agent.color,
                border: `1px solid ${agent.color}20`,
                lineHeight: 1.6,
              }}
            >
              {agent.outputSnippet}
            </div>
          )}

          {/* Running shimmer bar */}
          {agent.status === "running" && (
            <div
              className="mt-3 h-1 rounded-full overflow-hidden"
              style={{ background: "rgba(255,255,255,0.06)" }}
            >
              <div
                className="h-full rounded-full"
                style={{
                  background: `linear-gradient(90deg, transparent, ${agent.color}, transparent)`,
                  animation: "shimmer 1.5s infinite",
                  width: "40%",
                }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function CasePage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;
  const [agents, setAgents] = useState<AgentState[]>(makeAgents());
  const [currentAgent, setCurrentAgent] = useState(0);
  const [done, setDone] = useState(false);

  const completedCount = agents.filter((a) => a.status === "done").length;
  const progress = Math.round((completedCount / agents.length) * 100);

  // Simulate pipeline (replace with real SSE in production)
  useEffect(() => {
    const TIMINGS = [2200, 8000, 3500, 4000, 2000]; // ms per agent
    let agentIndex = 0;
    let startTime = Date.now();

    const runNext = () => {
      if (agentIndex >= agents.length) { setDone(true); return; }

      // Mark as running
      setCurrentAgent(agentIndex);
      setAgents((prev) =>
        prev.map((a, i) => (i === agentIndex ? { ...a, status: "running" } : a))
      );
      startTime = Date.now();

      setTimeout(() => {
        const elapsed = Date.now() - startTime;
        const idx = agentIndex;
        setAgents((prev) =>
          prev.map((a, i) =>
            i === idx
              ? {
                  ...a,
                  status: "done",
                  elapsed,
                  outputSnippet: MOCK_OUTPUTS[a.id],
                }
              : a
          )
        );
        agentIndex++;
        setTimeout(runNext, 300);
      }, TIMINGS[agentIndex]);
    };

    const t = setTimeout(runNext, 600);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-screen" style={{ background: "var(--purple-950)" }}>
      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-200%); }
          100% { transform: translateX(400%); }
        }
      `}</style>

      <div className="orb orb-1 fixed" style={{ opacity: 0.4 }} />

      {/* Header */}
      <header
        className="relative z-10 flex items-center justify-between px-6 py-5"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
      >
        <Link href="/" className="flex items-center gap-2">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{ background: "linear-gradient(135deg, #4f31b8, #8b6fe8)" }}
          >
            <ScaleIcon size={14} color="white" />
          </div>
          <span style={{ fontFamily: "var(--font-display)", fontSize: "1.1rem" }}>
            Advo<span className="gold-text">AI</span>
          </span>
        </Link>
        <span
          className="text-xs font-mono"
          style={{ color: "rgba(250,248,242,0.25)" }}
        >
          {sessionId}
        </span>
      </header>

      <main className="relative z-10 max-w-2xl mx-auto px-6 py-12">
        {/* Title */}
        <div className="text-center mb-10">
          <h1
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "clamp(1.8rem, 5vw, 2.8rem)",
              lineHeight: 1.1,
              marginBottom: "10px",
            }}
          >
            {done ? (
              <span className="gradient-text">Appeal ready.</span>
            ) : (
              <>Agents at work<span className="cursor" /></>
            )}
          </h1>
          <p className="text-sm" style={{ color: "rgba(250,248,242,0.4)" }}>
            {done
              ? "Your complete appeal packet has been generated."
              : "Five AI specialists are building your appeal in real time."}
          </p>
        </div>

        {/* Progress bar */}
        <div
          className="h-1.5 rounded-full mb-8 overflow-hidden"
          style={{ background: "rgba(255,255,255,0.06)" }}
        >
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${progress}%`,
              background: done
                ? "linear-gradient(90deg, #34d399, #6347d4)"
                : "linear-gradient(90deg, #6347d4, #8b6fe8)",
            }}
          />
        </div>
        <div
          className="flex items-center justify-between text-xs mb-10"
          style={{ color: "rgba(250,248,242,0.3)" }}
        >
          <span>{completedCount} of 5 agents complete</span>
          <span>{progress}%</span>
        </div>

        {/* Agent cards */}
        <div className="flex flex-col gap-4">
          {agents.map((agent, i) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              isActive={currentAgent === i && !done}
            />
          ))}
        </div>

        {/* Done CTA */}
        {done && (
          <div
            className="mt-10 rounded-3xl p-8 text-center"
            style={{
              background: "linear-gradient(135deg, rgba(79,49,184,0.2), rgba(52,211,153,0.08))",
              border: "1px solid rgba(52,211,153,0.25)",
            }}
          >
            <div
              className="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-5"
              style={{ background: "rgba(52,211,153,0.12)" }}
            >
              <CheckCircle size={28} color="#34d399" />
            </div>
            <h2
              style={{ fontFamily: "var(--font-display)", fontSize: "1.5rem", marginBottom: "8px" }}
            >
              Your appeal is ready
            </h2>
            <p className="text-sm mb-8" style={{ color: "rgba(250,248,242,0.5)" }}>
              The Judge scored your appeal 91/100 and recommends submission.
            </p>
            <button
              onClick={() => router.push(`/case/${sessionId}/letter`)}
              className="btn-primary inline-flex items-center gap-3 px-8 py-4 rounded-full text-sm font-medium text-white cursor-pointer"
            >
              <span>View your appeal letter</span>
              <span style={{ color: "var(--gold-light)" }}>→</span>
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
