"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getUser, getToken, clearAuth, authFetch } from "@/lib/auth";

// ─── Types ────────────────────────────────────────────────────────────────────

interface AgentStatus {
  auditor: "done" | "running" | "error" | "pending";
  clinician: "done" | "running" | "error" | "pending";
  regulatory: "done" | "running" | "error" | "pending";
  barrister: "done" | "running" | "error" | "pending";
  judge: "done" | "running" | "error" | "pending";
}

interface Case {
  id: string;
  patient_name: string;
  denial_reason: string;
  status: "pending" | "running" | "complete" | "error";
  agents: AgentStatus;
  judge_score: number | null;   // 0–100
  appeal_strength: "Weak" | "Moderate" | "Strong" | "Very Strong" | null;
  created_at: string;           // ISO string
  has_pdf: boolean;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const AGENTS: (keyof AgentStatus)[] = ["auditor", "clinician", "regulatory", "barrister", "judge"];

const AGENT_ICONS: Record<keyof AgentStatus, string> = {
  auditor:    "🔍",
  clinician:  "🩺",
  regulatory: "⚖️",
  barrister:  "📜",
  judge:      "🏛️",
};

const STRENGTH_COLOR: Record<string, string> = {
  "Weak":        "#f87171",
  "Moderate":    "#fbbf24",
  "Strong":      "#34d399",
  "Very Strong": "#4ade80",
};

// ─── Mock data (replace with real API once endpoint returns user-scoped cases) ─

const MOCK_CASES: Case[] = [
  {
    id: "case_001",
    patient_name: "Sarah Mitchell",
    denial_reason: "Prior authorization not obtained for MRI lumbar spine",
    status: "complete",
    agents: { auditor:"done", clinician:"done", regulatory:"done", barrister:"done", judge:"done" },
    judge_score: 84,
    appeal_strength: "Strong",
    created_at: new Date(Date.now() - 2 * 86400000).toISOString(),
    has_pdf: true,
  },
  {
    id: "case_002",
    patient_name: "James Okafor",
    denial_reason: "Experimental treatment — Keytruda off-label for Stage II NSCLC",
    status: "complete",
    agents: { auditor:"done", clinician:"done", regulatory:"done", barrister:"done", judge:"done" },
    judge_score: 91,
    appeal_strength: "Very Strong",
    created_at: new Date(Date.now() - 5 * 86400000).toISOString(),
    has_pdf: true,
  },
  {
    id: "case_003",
    patient_name: "Priya Nair",
    denial_reason: "Out-of-network facility — emergency cardiac catheterisation",
    status: "running",
    agents: { auditor:"done", clinician:"done", regulatory:"running", barrister:"pending", judge:"pending" },
    judge_score: null,
    appeal_strength: null,
    created_at: new Date(Date.now() - 1 * 3600000).toISOString(),
    has_pdf: false,
  },
  {
    id: "case_004",
    patient_name: "Carlos Reyes",
    denial_reason: "Medical necessity not established — sleep study (polysomnography)",
    status: "complete",
    agents: { auditor:"done", clinician:"done", regulatory:"done", barrister:"done", judge:"done" },
    judge_score: 67,
    appeal_strength: "Moderate",
    created_at: new Date(Date.now() - 10 * 86400000).toISOString(),
    has_pdf: true,
  },
  {
    id: "case_005",
    patient_name: "Amara Johnson",
    denial_reason: "Benefit not covered — bariatric surgery BMI 38",
    status: "error",
    agents: { auditor:"done", clinician:"error", regulatory:"pending", barrister:"pending", judge:"pending" },
    judge_score: null,
    appeal_strength: null,
    created_at: new Date(Date.now() - 3 * 86400000).toISOString(),
    has_pdf: false,
  },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days  = Math.floor(diff / 86400000);
  if (mins < 60)  return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
}

function scoreGradient(score: number): string {
  if (score >= 80) return "linear-gradient(90deg, #4f31b8, #34d399)";
  if (score >= 60) return "linear-gradient(90deg, #4f31b8, #fbbf24)";
  return "linear-gradient(90deg, #4f31b8, #f87171)";
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function AgentPipeline({ agents }: { agents: AgentStatus }) {
  return (
    <div style={{ display:"flex", alignItems:"center", gap:"4px", marginTop:"12px" }}>
      {AGENTS.map((agent, i) => {
        const st = agents[agent];
        const bg =
          st === "done"    ? "rgba(52,211,153,0.15)"  :
          st === "running" ? "rgba(139,111,232,0.25)" :
          st === "error"   ? "rgba(248,113,113,0.15)" :
                             "rgba(255,255,255,0.05)";
        const border =
          st === "done"    ? "1px solid rgba(52,211,153,0.35)"  :
          st === "running" ? "1px solid rgba(139,111,232,0.5)"  :
          st === "error"   ? "1px solid rgba(248,113,113,0.35)" :
                             "1px solid rgba(255,255,255,0.08)";
        const opacity = st === "pending" ? 0.4 : 1;
        return (
          <div key={agent} style={{ display:"flex", alignItems:"center", gap:"4px" }}>
            <div
              title={`${agent} — ${st}`}
              style={{ background:bg, border, borderRadius:"8px", padding:"4px 7px", fontSize:"0.7rem", opacity, display:"flex", alignItems:"center", gap:"4px", whiteSpace:"nowrap" }}
            >
              <span>{AGENT_ICONS[agent]}</span>
              {st === "running" && <span style={{ display:"inline-block", width:"6px", height:"6px", borderRadius:"50%", background:"#8b6fe8", animation:"pulse 1s ease-in-out infinite" }} />}
              {st === "error"   && <span style={{ color:"#f87171", fontSize:"0.65rem" }}>✕</span>}
            </div>
            {i < AGENTS.length - 1 && (
              <div style={{ width:"12px", height:"1px", background:"rgba(255,255,255,0.1)" }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function StatusBadge({ status }: { status: Case["status"] }) {
  const map = {
    complete: { label:"Complete",  bg:"rgba(52,211,153,0.12)",  border:"rgba(52,211,153,0.3)",  color:"#34d399" },
    running:  { label:"Running",   bg:"rgba(139,111,232,0.15)", border:"rgba(139,111,232,0.4)", color:"#a78bfa" },
    error:    { label:"Error",     bg:"rgba(248,113,113,0.12)", border:"rgba(248,113,113,0.3)", color:"#f87171" },
    pending:  { label:"Pending",   bg:"rgba(255,255,255,0.05)", border:"rgba(255,255,255,0.1)", color:"rgba(250,248,242,0.4)" },
  };
  const s = map[status];
  return (
    <span style={{ fontSize:"0.7rem", fontWeight:600, letterSpacing:"0.06em", textTransform:"uppercase", padding:"3px 10px", borderRadius:"999px", background:s.bg, border:`1px solid ${s.border}`, color:s.color }}>
      {s.label}
    </span>
  );
}

// ─── Case card ────────────────────────────────────────────────────────────────

function CaseCard({ c, onDelete }: { c: Case; onDelete: (id: string) => void }) {
  const router = useRouter();
  const [deleting, setDeleting] = useState(false);
  const [hovered, setHovered] = useState(false);

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`Delete case for ${c.patient_name}? This cannot be undone.`)) return;
    setDeleting(true);
    try {
      await authFetch(`/api/case/${c.id}`, { method: "DELETE" });
      onDelete(c.id);
    } catch {
      alert("Failed to delete case.");
      setDeleting(false);
    }
  };

  const handleDownload = async (e: React.MouseEvent) => {
    e.stopPropagation();
    const token = getToken();
    window.open(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/case/${c.id}/download?token=${token}`, "_blank");
  };

  return (
    <div
      onClick={() => router.push(`/case/${c.id}`)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
        border: hovered ? "1px solid rgba(139,111,232,0.35)" : "1px solid rgba(255,255,255,0.07)",
        borderRadius: "20px",
        padding: "24px",
        cursor: "pointer",
        transition: "all 0.2s ease",
        boxShadow: hovered ? "0 8px 40px rgba(79,49,184,0.2)" : "none",
        position: "relative",
        display: "flex",
        flexDirection: "column",
        gap: "0",
      }}
    >
      {/* Top row: name + status badge */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:"8px" }}>
        <div>
          <p style={{ margin:0, fontSize:"0.7rem", color:"rgba(250,248,242,0.35)", letterSpacing:"0.08em", textTransform:"uppercase", fontWeight:500 }}>
            {c.id}
          </p>
          <h3 style={{ margin:"4px 0 0", fontFamily:"'DM Serif Display', serif", fontSize:"1.1rem", fontWeight:400, color:"#faf8f2", letterSpacing:"-0.2px" }}>
            {c.patient_name}
          </h3>
        </div>
        <StatusBadge status={c.status} />
      </div>

      {/* Denial reason */}
      <p style={{ margin:"0 0 0", fontSize:"0.8125rem", color:"rgba(250,248,242,0.5)", lineHeight:1.5, display:"-webkit-box", WebkitLineClamp:2, WebkitBoxOrient:"vertical", overflow:"hidden" }}>
        {c.denial_reason}
      </p>

      {/* Agent pipeline */}
      <AgentPipeline agents={c.agents} />

      {/* Judge score */}
      {c.judge_score !== null && c.appeal_strength ? (
        <div style={{ marginTop:"16px" }}>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"6px" }}>
            <span style={{ fontSize:"0.75rem", color:"rgba(250,248,242,0.45)", letterSpacing:"0.03em" }}>Appeal Strength</span>
            <span style={{ fontSize:"0.8125rem", fontWeight:600, color: STRENGTH_COLOR[c.appeal_strength] }}>
              {c.appeal_strength} — {c.judge_score}/100
            </span>
          </div>
          <div style={{ height:"4px", borderRadius:"999px", background:"rgba(255,255,255,0.08)", overflow:"hidden" }}>
            <div style={{ height:"100%", width:`${c.judge_score}%`, borderRadius:"999px", background: scoreGradient(c.judge_score), transition:"width 0.6s ease" }} />
          </div>
        </div>
      ) : (
        <div style={{ marginTop:"16px", height:"4px", borderRadius:"999px", background:"rgba(255,255,255,0.05)" }} />
      )}

      {/* Bottom row: date + actions */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginTop:"16px" }}>
        <span style={{ fontSize:"0.75rem", color:"rgba(250,248,242,0.3)" }}>{timeAgo(c.created_at)}</span>

        <div style={{ display:"flex", gap:"8px" }} onClick={(e) => e.stopPropagation()}>
          {c.has_pdf && (
            <button
              onClick={handleDownload}
              title="Download PDF packet"
              style={{ padding:"6px 12px", background:"rgba(201,168,76,0.12)", border:"1px solid rgba(201,168,76,0.25)", borderRadius:"8px", color:"#e8c97a", fontSize:"0.75rem", fontWeight:500, cursor:"pointer", fontFamily:"'DM Sans', sans-serif", transition:"all 0.15s" }}
            >
              ↓ PDF
            </button>
          )}
          <button
            onClick={handleDelete}
            disabled={deleting}
            title="Delete case"
            style={{ padding:"6px 10px", background:"rgba(248,113,113,0.08)", border:"1px solid rgba(248,113,113,0.18)", borderRadius:"8px", color:"#f87171", fontSize:"0.75rem", cursor:deleting?"not-allowed":"pointer", fontFamily:"'DM Sans', sans-serif", opacity: deleting ? 0.5 : 1, transition:"all 0.15s" }}
          >
            {deleting ? "…" : "✕"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Stats bar ────────────────────────────────────────────────────────────────

function StatsBar({ cases }: { cases: Case[] }) {
  const total    = cases.length;
  const complete = cases.filter(c => c.status === "complete").length;
  const running  = cases.filter(c => c.status === "running").length;
  const avgScore = (() => {
    const scored = cases.filter(c => c.judge_score !== null);
    if (!scored.length) return null;
    return Math.round(scored.reduce((a, c) => a + (c.judge_score ?? 0), 0) / scored.length);
  })();

  const stats = [
    { label:"Total Cases",    value: total,                 sub: "submitted" },
    { label:"Completed",      value: complete,              sub: `${total ? Math.round(complete/total*100) : 0}% success rate` },
    { label:"In Progress",    value: running,               sub: "running now" },
    { label:"Avg. Score",     value: avgScore ?? "—",       sub: "judge rating" },
  ];

  return (
    <div style={{ display:"grid", gridTemplateColumns:"repeat(4, 1fr)", gap:"16px", marginBottom:"40px" }}>
      {stats.map(s => (
        <div key={s.label} style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"16px", padding:"20px 24px" }}>
          <p style={{ margin:0, fontSize:"0.75rem", color:"rgba(250,248,242,0.4)", letterSpacing:"0.06em", textTransform:"uppercase", fontWeight:500 }}>{s.label}</p>
          <p style={{ margin:"6px 0 4px", fontFamily:"'DM Serif Display', serif", fontSize:"2rem", fontWeight:400, color:"#faf8f2", lineHeight:1 }}>{s.value}</p>
          <p style={{ margin:0, fontSize:"0.75rem", color:"rgba(250,248,242,0.3)" }}>{s.sub}</p>
        </div>
      ))}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const router = useRouter();
  const [cases, setCases]   = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "complete" | "running" | "error">("all");
  const user = getUser();

  useEffect(() => {
    if (!getToken()) { router.push("/login"); return; }
    fetchCases();
  }, []);

  async function fetchCases() {
    setLoading(true);
    try {
      const res = await authFetch("/api/cases");
      if (res.ok) {
        const data = await res.json();
        setCases(data.cases ?? []);
      } else {
        // Fall back to mock data while backend endpoint isn't scoped yet
        setCases(MOCK_CASES);
      }
    } catch {
      setCases(MOCK_CASES);
    } finally {
      setLoading(false);
    }
  }

  function handleDelete(id: string) {
    setCases(prev => prev.filter(c => c.id !== id));
  }

  const visible = filter === "all" ? cases : cases.filter(c => c.status === filter);

  return (
    <main style={{ minHeight:"100vh", background:"#0f0a1e", fontFamily:"'DM Sans', sans-serif", color:"#faf8f2" }}>
      {/* Ambient orbs */}
      <div style={{ position:"fixed", top:"-200px", right:"-200px", width:"600px", height:"600px", borderRadius:"50%", background:"radial-gradient(circle, rgba(79,49,184,0.15) 0%, transparent 70%)", pointerEvents:"none", zIndex:0 }} />
      <div style={{ position:"fixed", bottom:"-100px", left:"-100px", width:"400px", height:"400px", borderRadius:"50%", background:"radial-gradient(circle, rgba(139,111,232,0.1) 0%, transparent 70%)", pointerEvents:"none", zIndex:0 }} />

      <div style={{ position:"relative", zIndex:1, maxWidth:"1200px", margin:"0 auto", padding:"40px 32px" }}>

        {/* Header */}
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:"40px" }}>
          <div>
            <Link href="/" style={{ textDecoration:"none" }}>
              <h1 style={{ fontFamily:"'DM Serif Display', serif", fontSize:"1.5rem", fontWeight:400, margin:"0 0 4px", color:"#faf8f2", letterSpacing:"-0.3px" }}>
                Advo<span style={{ background:"linear-gradient(135deg, #c9a84c, #e8c97a)", WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent", backgroundClip:"text" }}>AI</span>
              </h1>
            </Link>
            <p style={{ margin:0, fontSize:"0.875rem", color:"rgba(250,248,242,0.4)" }}>
              {user ? `Welcome back, ${user.name.split(" ")[0]}` : "Your cases"}
            </p>
          </div>

          <div style={{ display:"flex", gap:"12px", alignItems:"center" }}>
            <button
              onClick={() => { clearAuth(); router.push("/login"); }}
              style={{ padding:"8px 16px", background:"transparent", border:"1px solid rgba(255,255,255,0.1)", borderRadius:"10px", color:"rgba(250,248,242,0.4)", fontSize:"0.8125rem", cursor:"pointer", fontFamily:"'DM Sans', sans-serif", transition:"all 0.15s" }}
            >
              Sign out
            </button>
            <Link
              href="/submit"
              style={{ padding:"10px 20px", background:"linear-gradient(135deg, #4f31b8, #8b6fe8)", color:"#faf8f2", textDecoration:"none", borderRadius:"12px", fontSize:"0.875rem", fontWeight:600, letterSpacing:"0.02em", boxShadow:"0 4px 20px rgba(79,49,184,0.35)", whiteSpace:"nowrap" }}
            >
              + New Case
            </Link>
          </div>
        </div>

        {/* Gold divider */}
        <div style={{ height:"1px", background:"linear-gradient(90deg, transparent, rgba(201,168,76,0.2), transparent)", marginBottom:"40px" }} />

        {/* Stats bar */}
        {!loading && <StatsBar cases={cases} />}

        {/* Filter tabs */}
        <div style={{ display:"flex", gap:"8px", marginBottom:"28px" }}>
          {(["all","complete","running","error"] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding:"7px 18px",
                borderRadius:"999px",
                border: filter === f ? "1px solid rgba(139,111,232,0.5)" : "1px solid rgba(255,255,255,0.08)",
                background: filter === f ? "rgba(79,49,184,0.2)" : "transparent",
                color: filter === f ? "#c4b5fd" : "rgba(250,248,242,0.4)",
                fontSize:"0.8125rem",
                fontWeight: filter === f ? 600 : 400,
                cursor:"pointer",
                fontFamily:"'DM Sans', sans-serif",
                textTransform:"capitalize",
                transition:"all 0.15s",
              }}
            >
              {f}
            </button>
          ))}
          <span style={{ marginLeft:"auto", fontSize:"0.8125rem", color:"rgba(250,248,242,0.3)", alignSelf:"center" }}>
            {visible.length} case{visible.length !== 1 ? "s" : ""}
          </span>
        </div>

        {/* Card grid */}
        {loading ? (
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(340px, 1fr))", gap:"20px" }}>
            {[1,2,3].map(i => (
              <div key={i} style={{ height:"260px", background:"rgba(255,255,255,0.02)", border:"1px solid rgba(255,255,255,0.05)", borderRadius:"20px", animation:"shimmer 1.5s ease-in-out infinite" }} />
            ))}
          </div>
        ) : visible.length === 0 ? (
          <div style={{ textAlign:"center", padding:"80px 0" }}>
            <p style={{ fontSize:"2rem", marginBottom:"12px" }}>📂</p>
            <p style={{ color:"rgba(250,248,242,0.3)", fontSize:"0.9375rem" }}>
              {filter === "all" ? "No cases yet." : `No ${filter} cases.`}
            </p>
            {filter === "all" && (
              <Link href="/submit" style={{ display:"inline-block", marginTop:"16px", padding:"10px 24px", background:"linear-gradient(135deg, #4f31b8, #8b6fe8)", color:"#faf8f2", textDecoration:"none", borderRadius:"12px", fontSize:"0.875rem", fontWeight:600 }}>
                Submit your first case
              </Link>
            )}
          </div>
        ) : (
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(340px, 1fr))", gap:"20px" }}>
            {visible.map((c, i) => (
              <div key={c.id} style={{ animation:`fadeUp 0.4s ease both`, animationDelay:`${i * 60}ms` }}>
                <CaseCard c={c} onDelete={handleDelete} />
              </div>
            ))}
          </div>
        )}
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600&display=swap');
        @keyframes fadeUp   { from { opacity:0; transform:translateY(16px) } to { opacity:1; transform:translateY(0) } }
        @keyframes pulse    { 0%,100% { opacity:1 } 50% { opacity:0.3 } }
        @keyframes shimmer  { 0%,100% { opacity:0.5 } 50% { opacity:1 } }
        input::placeholder { color: rgba(250,248,242,0.25); }
      `}</style>
    </main>
  );
}
