"use client";

const STEPS = [
  { number: 1, label: "Denial letter" },
  { number: 2, label: "Policy PDF" },
  { number: 3, label: "Case details" },
  { number: 4, label: "Review" },
];

export default function StepIndicator({ currentStep }: { currentStep: number }) {
  return (
    <>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "center", marginBottom: "2.5rem" }}>
        {STEPS.map((step, i) => {
          const isDone = currentStep > step.number;
          const isActive = currentStep === step.number;
          return (
            <div key={step.number} style={{ display: "flex", alignItems: "center" }}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem" }}>
                <div style={{
                  width: "2.25rem", height: "2.25rem", borderRadius: "50%",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "0.875rem", fontWeight: 500,
                  transition: "all 0.4s ease",
                  background: isDone ? "linear-gradient(135deg, #4f31b8, #8b6fe8)" : isActive ? "rgba(99,71,212,0.2)" : "rgba(255,255,255,0.05)",
                  border: isDone ? "1px solid rgba(179,158,244,0.5)" : isActive ? "1px solid #8b6fe8" : "1px solid rgba(255,255,255,0.1)",
                  color: isDone ? "white" : isActive ? "#b39ef4" : "rgba(250,248,242,0.3)",
                  boxShadow: isActive ? "0 0 16px rgba(99,71,212,0.4)" : "none",
                }}>
                  {isDone ? (
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                      <path d="M2 7l3.5 3.5L12 3.5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  ) : step.number}
                </div>
                <span className="step-label" style={{
                  fontSize: "0.7rem", whiteSpace: "nowrap",
                  color: isActive ? "var(--purple-300)" : isDone ? "rgba(250,248,242,0.5)" : "rgba(250,248,242,0.2)",
                  fontWeight: isActive ? 500 : 400,
                }}>
                  {step.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div className="step-connector" style={{
                  height: "1px", margin: "0 6px", marginBottom: "1.5rem",
                  transition: "all 0.5s ease",
                  background: isDone ? "linear-gradient(90deg, #6347d4, #8b6fe8)" : "rgba(255,255,255,0.08)",
                }} />
              )}
            </div>
          );
        })}
      </div>
      <style>{`
        .step-connector { width: 28px; }
        .step-label { display: none; }
        @media (min-width: 400px) { .step-connector { width: 44px; } .step-label { display: block; } }
        @media (min-width: 640px) { .step-connector { width: 72px; } }
      `}</style>
    </>
  );
}