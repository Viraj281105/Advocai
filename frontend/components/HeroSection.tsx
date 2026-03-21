"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, FileText, Shield } from "lucide-react";

const ROTATING_WORDS = ["Denied.", "Appealed.", "Approved."];
const COLORS = ["#f87171", "#fbbf24", "#34d399"];

export default function HeroSection() {
  const [wordIndex, setWordIndex] = useState(0);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setVisible(false);
      setTimeout(() => { setWordIndex(i => (i + 1) % ROTATING_WORDS.length); setVisible(true); }, 400);
    }, 2200);
    return () => clearInterval(interval);
  }, []);

  return (
    <section style={{ position: "relative", minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center", padding: "6rem 1.5rem 5rem", overflow: "hidden" }}>
      <div className="orb orb-1" />
      <div className="orb orb-2" />

      {/* Badge */}
      <div className="fade-up" style={{ animationDelay: "0.1s", opacity: 0, background: "rgba(255,255,255,0.03)", backdropFilter: "blur(12px)", border: "1px solid rgba(255,255,255,0.07)", display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.5rem 1rem", borderRadius: "9999px", marginBottom: "2.5rem" }}>
        <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#34d399", display: "inline-block" }} className="pulse-ring" />
        <span style={{ fontSize: "0.875rem", color: "rgba(250,248,242,0.7)" }}>5 AI agents working in parallel</span>
      </div>

      {/* Headline */}
      <h1 className="fade-up" style={{ fontFamily: "var(--font-display)", fontSize: "clamp(3rem, 8vw, 6.5rem)", lineHeight: 1.05, letterSpacing: "-0.02em", maxWidth: "900px", animationDelay: "0.2s", opacity: 0 }}>
        Your claim was{" "}
        <span style={{ color: COLORS[wordIndex], transition: "opacity 0.4s ease, transform 0.4s ease", opacity: visible ? 1 : 0, display: "inline-block", transform: visible ? "translateY(0)" : "translateY(-8px)", fontStyle: "italic" }}>
          {ROTATING_WORDS[wordIndex]}
        </span>
        <br />
        <span className="gradient-text">We fight back.</span>
      </h1>

      {/* Subtext */}
      <p className="fade-up" style={{ marginTop: "2rem", maxWidth: "640px", fontSize: "1.1rem", lineHeight: 1.7, color: "rgba(250,248,242,0.55)", animationDelay: "0.35s", opacity: 0 }}>
        AdvocAI deploys five specialized AI agents — Auditor, Clinician, Regulatory expert, Barrister, and Judge — to build a medically sound, legally airtight insurance appeal letter in under 30 seconds.
      </p>

      {/* CTAs */}
      <div className="fade-up" style={{ marginTop: "3rem", display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "center", gap: "1rem", animationDelay: "0.5s", opacity: 0 }}>
        <Link href="/submit" className="btn-primary" style={{ display: "inline-flex", alignItems: "center", gap: "0.75rem", padding: "1rem 2rem", borderRadius: "9999px", fontSize: "1rem", fontWeight: 500, color: "white", textDecoration: "none" }}>
          <span>Upload your denial PDF</span>
          <ArrowRight size={18} />
        </Link>
        <a href="#how-it-works" className="btn-secondary" style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "1rem 2rem", borderRadius: "9999px", fontSize: "1rem", fontWeight: 500, color: "var(--cream)", textDecoration: "none" }}>
          See how it works
        </a>
      </div>

      {/* Trust indicators */}
      <div className="fade-up" style={{ marginTop: "3.5rem", display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "center", gap: "1.5rem", animationDelay: "0.65s", opacity: 0 }}>
        {[
          { icon: <Shield size={14} />, text: "No PHI stored or logged" },
          { icon: <FileText size={14} />, text: "PubMed-backed medical evidence" },
          { icon: "⚖️", text: "ACA & ERISA statute coverage" },
        ].map((item, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.875rem", color: "rgba(250,248,242,0.4)" }}>
            <span style={{ color: "var(--purple-400)" }}>{item.icon}</span>
            {item.text}
          </div>
        ))}
      </div>

      {/* Scroll hint */}
      <div className="fade-up" style={{ position: "absolute", bottom: "2.5rem", left: "50%", transform: "translateX(-50%)", display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem", animationDelay: "1s", opacity: 0 }}>
        <span style={{ fontSize: "0.7rem", color: "rgba(250,248,242,0.25)" }}>scroll</span>
        <div style={{ width: "1px", height: "2rem", background: "linear-gradient(180deg, rgba(179,158,244,0.4), transparent)" }} />
      </div>
    </section>
  );
}
