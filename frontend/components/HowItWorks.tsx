"use client";
import { Upload, Cpu, FileCheck } from "lucide-react";

const STEPS = [
  { icon: Upload,    color: "#8b6fe8", title: "Upload your PDFs",      description: "Drop in your insurance denial letter and your policy document. That's all the input we need." },
  { icon: Cpu,       color: "#34d399", title: "Agents go to work",     description: "Five AI agents run in sequence — parsing, researching PubMed, citing statutes, drafting, and scoring your appeal." },
  { icon: FileCheck, color: "#fbbf24", title: "Download & submit",     description: "Receive a complete, professional appeal packet — letter, evidence, legal brief, and QA scorecard — ready to send." },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" style={{ position: "relative", padding: "clamp(3rem, 8vw, 6rem) 1.25rem" }}>
      <div className="orb orb-3" />
      <div style={{ maxWidth: "1280px", margin: "0 auto" }}>
        <div style={{ textAlign: "center", marginBottom: "5rem" }}>
          <p style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.15em", color: "var(--purple-400)", fontWeight: 500, marginBottom: "1rem" }}>How it works</p>
          <h2 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(2rem, 5vw, 3.5rem)", lineHeight: 1.1, letterSpacing: "-0.02em" }}>
            From denial to appeal{" "}<span className="gold-text">in 30 seconds.</span>
          </h2>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "2rem" }}>
          {STEPS.map((step, i) => {
            const Icon = step.icon;
            return (
              <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center", gap: "1.5rem" }}>
                <div style={{ position: "relative" }}>
                  <div style={{ width: "5rem", height: "5rem", borderRadius: "9999px", display: "flex", alignItems: "center", justifyContent: "center", background: `${step.color}15`, border: `1px solid ${step.color}30` }}>
                    <Icon size={30} color={step.color} />
                  </div>
                  <span style={{ position: "absolute", top: "-4px", right: "-4px", width: "1.5rem", height: "1.5rem", borderRadius: "9999px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.7rem", fontWeight: "bold", background: "var(--purple-950)", border: `1px solid ${step.color}60`, color: step.color }}>
                    {i + 1}
                  </span>
                </div>
                <div>
                  <h3 style={{ fontFamily: "var(--font-display)", fontSize: "1.3rem", marginBottom: "0.625rem" }}>{step.title}</h3>
                  <p style={{ fontSize: "0.875rem", lineHeight: 1.7, color: "rgba(250,248,242,0.5)", maxWidth: "280px", margin: "0 auto" }}>{step.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
