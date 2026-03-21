"use client";
import Link from "next/link";
import { Scale, Github } from "lucide-react";

export default function Footer() {
  return (
    <footer style={{ position: "relative", borderTop: "1px solid rgba(255,255,255,0.07)", padding: "3rem 1.5rem" }}>
      <div style={{ maxWidth: "1280px", margin: "0 auto", display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: "1.5rem" }}>
        <Link href="/" style={{ display: "flex", alignItems: "center", gap: "0.5rem", textDecoration: "none" }}>
          <div style={{ width: "1.75rem", height: "1.75rem", borderRadius: "0.5rem", display: "flex", alignItems: "center", justifyContent: "center", background: "linear-gradient(135deg, #4f31b8, #8b6fe8)" }}>
            <Scale size={14} color="white" />
          </div>
          <span style={{ fontFamily: "var(--font-display)", fontSize: "1.1rem", color: "var(--cream)" }}>
            Advo<span className="gold-text">AI</span>
          </span>
        </Link>
        <div style={{ display: "flex", alignItems: "center", gap: "1.5rem", fontSize: "0.875rem", color: "rgba(250,248,242,0.4)" }}>
          <span>MIT License</span>
          <span>·</span>
          <span>Built for Kaggle Agents Intensive</span>
          <span>·</span>
          <a href="https://github.com/Viraj281105/Advocai" target="_blank" rel="noopener noreferrer"
            style={{ display: "flex", alignItems: "center", gap: "0.25rem", color: "rgba(250,248,242,0.4)", textDecoration: "none", transition: "color 0.2s" }}
            onMouseEnter={e => (e.currentTarget.style.color = "var(--cream)")}
            onMouseLeave={e => (e.currentTarget.style.color = "rgba(250,248,242,0.4)")}>
            <Github size={14} />
            GitHub
          </a>
        </div>
      </div>
    </footer>
  );
}
