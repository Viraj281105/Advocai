"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiRegister, saveAuth } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      const { token, user } = await apiRegister(form.name, form.email, form.password);
      saveAuth(token, user);
      router.push("/dashboard"); // → Issue #10 case dashboard
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ minHeight:"100vh", background:"#0f0a1e", display:"flex", alignItems:"center", justifyContent:"center", padding:"24px", position:"relative", overflow:"hidden", fontFamily:"'DM Sans', sans-serif" }}>
      <div style={{ position:"absolute", top:"-120px", left:"-120px", width:"480px", height:"480px", borderRadius:"50%", background:"radial-gradient(circle, rgba(79,49,184,0.28) 0%, transparent 70%)", pointerEvents:"none" }} />
      <div style={{ position:"absolute", bottom:"-80px", right:"-80px", width:"360px", height:"360px", borderRadius:"50%", background:"radial-gradient(circle, rgba(139,111,232,0.18) 0%, transparent 70%)", pointerEvents:"none" }} />
      <div style={{ position:"absolute", top:"40%", right:"10%", width:"200px", height:"200px", borderRadius:"50%", background:"radial-gradient(circle, rgba(201,168,76,0.08) 0%, transparent 70%)", pointerEvents:"none" }} />

      <div style={{ width:"100%", maxWidth:"440px", background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:"24px", backdropFilter:"blur(20px)", WebkitBackdropFilter:"blur(20px)", padding:"48px 40px", boxShadow:"0 32px 80px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06)", position:"relative", zIndex:1 }}>

        <div style={{ textAlign:"center", marginBottom:"32px" }}>
          <Link href="/" style={{ textDecoration:"none" }}>
            <h1 style={{ fontFamily:"'DM Serif Display', serif", fontSize:"2rem", fontWeight:400, color:"#faf8f2", margin:0, letterSpacing:"-0.5px" }}>
              <span>Advo</span>
              <span style={{ background:"linear-gradient(135deg, #c9a84c, #e8c97a)", WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent", backgroundClip:"text" }}>AI</span>
            </h1>
          </Link>
          <p style={{ color:"rgba(250,248,242,0.45)", fontSize:"0.875rem", margin:"8px 0 0" }}>Create your account</p>
        </div>

        <div style={{ height:"1px", background:"linear-gradient(90deg, transparent, rgba(201,168,76,0.25), transparent)", marginBottom:"32px" }} />

        <form onSubmit={handleSubmit} style={{ display:"flex", flexDirection:"column", gap:"18px" }}>
          {[
            { name:"name",    type:"text",     label:"Full Name",        placeholder:"Jane Smith" },
            { name:"email",   type:"email",    label:"Email Address",    placeholder:"jane@example.com" },
            { name:"password",type:"password", label:"Password",         placeholder:"At least 8 characters" },
            { name:"confirm", type:"password", label:"Confirm Password", placeholder:"Repeat your password" },
          ].map(({ name, type, label, placeholder }) => (
            <div key={name}>
              <label style={labelStyle}>{label}</label>
              <input
                name={name}
                type={type}
                required
                placeholder={placeholder}
                value={form[name as keyof typeof form]}
                onChange={handleChange}
                style={inputStyle}
                onFocus={(e) => Object.assign(e.target.style, inputFocusStyle)}
                onBlur={(e)  => Object.assign(e.target.style, inputStyle)}
              />
            </div>
          ))}

          {error && <p style={errorStyle}>{error}</p>}

          <button type="submit" disabled={loading} style={{ ...btnStyle, background: loading ? "rgba(79,49,184,0.4)" : "linear-gradient(135deg, #4f31b8, #8b6fe8)", cursor: loading ? "not-allowed" : "pointer", boxShadow: loading ? "none" : "0 4px 24px rgba(79,49,184,0.4)" }}>
            {loading ? <><span style={spinnerStyle} />Creating account…</> : "Create Account"}
          </button>
        </form>

        <p style={{ textAlign:"center", marginTop:"28px", fontSize:"0.875rem", color:"rgba(250,248,242,0.4)" }}>
          Already have an account?{" "}
          <Link href="/login" style={{ color:"#e8c97a", textDecoration:"none", fontWeight:500 }}>Sign in</Link>
        </p>
      </div>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600&display=swap'); @keyframes spin{to{transform:rotate(360deg)}}`}</style>
    </main>
  );
}

const labelStyle: React.CSSProperties = { display:"block", fontSize:"0.8125rem", fontWeight:500, color:"rgba(250,248,242,0.6)", marginBottom:"8px", letterSpacing:"0.03em" };
const inputStyle: React.CSSProperties = { width:"100%", padding:"12px 16px", background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:"12px", color:"#faf8f2", fontFamily:"'DM Sans', sans-serif", fontSize:"0.9375rem", outline:"none", transition:"border-color 0.2s, background 0.2s", boxSizing:"border-box" };
const inputFocusStyle: React.CSSProperties = { ...inputStyle, borderColor:"rgba(139,111,232,0.6)", background:"rgba(79,49,184,0.1)" };
const btnStyle: React.CSSProperties = { marginTop:"8px", padding:"14px", color:"#faf8f2", border:"none", borderRadius:"12px", fontFamily:"'DM Sans', sans-serif", fontSize:"0.9375rem", fontWeight:600, letterSpacing:"0.02em", transition:"all 0.2s ease", display:"flex", alignItems:"center", justifyContent:"center", gap:"8px" };
const spinnerStyle: React.CSSProperties = { display:"inline-block", width:"16px", height:"16px", border:"2px solid rgba(255,255,255,0.3)", borderTopColor:"#fff", borderRadius:"50%", animation:"spin 0.7s linear infinite" };
const errorStyle: React.CSSProperties = { color:"#f87171", fontSize:"0.8125rem", margin:0, padding:"10px 14px", background:"rgba(248,113,113,0.08)", border:"1px solid rgba(248,113,113,0.2)", borderRadius:"10px" };
