"use client";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

export default function CTASection() {
  return (
    <section style={{ position: "relative", padding: "8rem 1.5rem", textAlign: "center", overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: 0, background: "radial-gradient(ellipse 80% 60% at 50% 50%, rgba(79,49,184,0.25) 0%, transparent 70%)", pointerEvents: "none" }} />
      <div style={{ position: "relative", maxWidth: "768px", margin: "0 auto" }}>
        <p style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.15em", color: "var(--purple-400)", fontWeight: 500, marginBottom: "1.5rem" }}>Ready?</p>
        <h2 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(2.5rem, 6vw, 4.5rem)", lineHeight: 1.05, letterSpacing: "-0.02em" }}>
          Stop leaving money{" "}<span className="gradient-text">on the table.</span>
        </h2>
        <p style={{ marginTop: "1.5rem", fontSize: "1.1rem", lineHeight: 1.7, color: "rgba(250,248,242,0.5)" }}>
          45% of appealed insurance claims are overturned. Your denial isn't final — it's just the beginning.
        </p>
        <div style={{ marginTop: "3rem", display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "center", gap: "1rem" }}>
          <Link href="/submit" className="btn-primary" style={{ display: "inline-flex", alignItems: "center", gap: "0.75rem", padding: "1.25rem 2.5rem", borderRadius: "9999px", fontSize: "1.1rem", fontWeight: 500, color: "white", textDecoration: "none" }}>
            <span>Start your appeal — free</span>
            <ArrowRight size={20} />
          </Link>
        </div>
        <p style={{ marginTop: "1.5rem", fontSize: "0.875rem", color: "rgba(250,248,242,0.25)" }}>
          No account required. No PHI stored. Open source under MIT.
        </p>
      </div>
    </section>
  );
}
