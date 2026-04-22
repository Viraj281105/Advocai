"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { apiLogin, saveAuth } from "@/lib/auth";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // 🔥 Get redirect target (VERY IMPORTANT)
  const next = searchParams.get("next") || "/dashboard";

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  console.log("🔥 Submit triggered");

  setLoading(true);

  try {
    console.log("📡 Calling API...");
    const { token, user } = await apiLogin(form.email, form.password);

    console.log("✅ Login success:", token, user);

    saveAuth(token, user);

    console.log("🚀 Redirecting...");
    console.log("🚀 Redirecting to:", next);
    router.replace(next);
    router.refresh();
  } catch (err) {
    console.error("❌ Login error:", err);
    setError(err instanceof Error ? err.message : "Login failed");
  } finally {
    setLoading(false);
  }
};

  return (
    <main style={{ minHeight:"100vh", background:"#0f0a1e", display:"flex", alignItems:"center", justifyContent:"center", padding:"24px", position:"relative", overflow:"hidden", fontFamily:"'DM Sans', sans-serif" }}>
      <div style={{ position:"absolute", top:"-100px", right:"-100px", width:"500px", height:"500px", borderRadius:"50%", background:"radial-gradient(circle, rgba(79,49,184,0.25) 0%, transparent 70%)", pointerEvents:"none" }} />
      <div style={{ position:"absolute", bottom:"-60px", left:"-60px", width:"380px", height:"380px", borderRadius:"50%", background:"radial-gradient(circle, rgba(139,111,232,0.15) 0%, transparent 70%)", pointerEvents:"none" }} />
      <div style={{ position:"absolute", top:"20%", left:"12%", width:"180px", height:"180px", borderRadius:"50%", background:"radial-gradient(circle, rgba(201,168,76,0.07) 0%, transparent 70%)", pointerEvents:"none" }} />

      <div style={{ width:"100%", maxWidth:"420px", background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:"24px", backdropFilter:"blur(20px)", WebkitBackdropFilter:"blur(20px)", padding:"48px 40px", boxShadow:"0 32px 80px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06)", position:"relative", zIndex:1 }}>

        <div style={{ textAlign:"center", marginBottom:"32px" }}>
          <Link href="/" style={{ textDecoration:"none" }}>
            <h1 style={{ fontFamily:"'DM Serif Display', serif", fontSize:"2rem", fontWeight:400, color:"#faf8f2", margin:0, letterSpacing:"-0.5px" }}>
              <span>Advo</span>
              <span style={{ background:"linear-gradient(135deg, #c9a84c, #e8c97a)", WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent", backgroundClip:"text" }}>AI</span>
            </h1>
          </Link>
          <p style={{ color:"rgba(250,248,242,0.45)", fontSize:"0.875rem", margin:"8px 0 0" }}>Welcome back</p>
        </div>

        <div style={{ height:"1px", background:"linear-gradient(90deg, transparent, rgba(201,168,76,0.25), transparent)", marginBottom:"32px" }} />

        <form onSubmit={handleSubmit} style={{ display:"flex", flexDirection:"column", gap:"18px" }}>
          <div>
            <label style={labelStyle}>Email Address</label>
            <input name="email" type="email" required placeholder="jane@example.com" value={form.email} onChange={handleChange} style={inputStyle} onFocus={(e)=>Object.assign(e.target.style,inputFocusStyle)} onBlur={(e)=>Object.assign(e.target.style,inputStyle)} />
          </div>

          <div>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"baseline" }}>
              <label style={labelStyle}>Password</label>
              <Link href="/forgot-password" style={{ fontSize:"0.75rem", color:"rgba(232,201,122,0.7)", textDecoration:"none", marginBottom:"8px" }}>Forgot password?</Link>
            </div>
            <input name="password" type="password" required placeholder="Your password" value={form.password} onChange={handleChange} style={inputStyle} onFocus={(e)=>Object.assign(e.target.style,inputFocusStyle)} onBlur={(e)=>Object.assign(e.target.style,inputStyle)} />
          </div>

          {error && <p style={errorStyle}>{error}</p>}

          <button type="submit" disabled={loading} style={{ ...btnStyle, background: loading ? "rgba(79,49,184,0.4)" : "linear-gradient(135deg, #4f31b8, #8b6fe8)", cursor: loading ? "not-allowed" : "pointer", boxShadow: loading ? "none" : "0 4px 24px rgba(79,49,184,0.4)" }}>
            {loading ? <><span style={spinnerStyle} />Signing in…</> : "Sign In"}
          </button>
        </form>

        <p style={{ textAlign:"center", marginTop:"28px", fontSize:"0.875rem", color:"rgba(250,248,242,0.4)" }}>
          Don&apos;t have an account?{" "}
          <Link href="/register" style={{ color:"#e8c97a", textDecoration:"none", fontWeight:500 }}>Create one</Link>
        </p>
      </div>

      <style>{`@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600&display=swap'); @keyframes spin{to{transform:rotate(360deg)}}`}</style>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div style={{ minHeight: "100vh", background: "#0f0a1e", color: "#faf8f2", display: "flex", alignItems: "center", justifyContent: "center" }}>Loading...</div>}>
      <LoginForm />
    </Suspense>
  );
}


const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: "0.8125rem",
  fontWeight: 500,
  color: "rgba(250,248,242,0.6)",
  marginBottom: "8px",
  letterSpacing: "0.03em",
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "12px 16px",
  background: "rgba(255,255,255,0.05)",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: "12px",
  color: "#faf8f2",
  fontFamily: "'DM Sans', sans-serif",
  fontSize: "0.9375rem",
  outline: "none",
  transition: "border-color 0.2s, background 0.2s",
  boxSizing: "border-box",
};

const inputFocusStyle: React.CSSProperties = {
  ...inputStyle,
  borderColor: "rgba(139,111,232,0.6)",
  background: "rgba(79,49,184,0.1)",
};

const btnStyle: React.CSSProperties = {
  marginTop: "8px",
  padding: "14px",
  color: "#faf8f2",
  border: "none",
  borderRadius: "12px",
  fontFamily: "'DM Sans', sans-serif",
  fontSize: "0.9375rem",
  fontWeight: 600,
  letterSpacing: "0.02em",
  transition: "all 0.2s ease",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: "8px",
};

const spinnerStyle: React.CSSProperties = {
  display: "inline-block",
  width: "16px",
  height: "16px",
  border: "2px solid rgba(255,255,255,0.3)",
  borderTopColor: "#fff",
  borderRadius: "50%",
  animation: "spin 0.7s linear infinite",
};

const errorStyle: React.CSSProperties = {
  color: "#f87171",
  fontSize: "0.8125rem",
  margin: 0,
  padding: "10px 14px",
  background: "rgba(248,113,113,0.08)",
  border: "1px solid rgba(248,113,113,0.2)",
  borderRadius: "10px",
};