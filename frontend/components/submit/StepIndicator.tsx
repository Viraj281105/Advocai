"use client";

interface Step {
  number: number;
  label: string;
}

const STEPS: Step[] = [
  { number: 1, label: "Denial letter" },
  { number: 2, label: "Policy PDF" },
  { number: 3, label: "Case details" },
  { number: 4, label: "Review" },
];

interface Props {
  currentStep: number;
}

export default function StepIndicator({ currentStep }: Props) {
  return (
    <div className="flex items-center justify-center gap-0 mb-12">
      {STEPS.map((step, i) => {
        const isDone = currentStep > step.number;
        const isActive = currentStep === step.number;

        return (
          <div key={step.number} className="flex items-center">
            {/* Circle */}
            <div className="flex flex-col items-center gap-2">
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-medium transition-all duration-400"
                style={{
                  background: isDone
                    ? "linear-gradient(135deg, #4f31b8, #8b6fe8)"
                    : isActive
                    ? "rgba(99,71,212,0.2)"
                    : "rgba(255,255,255,0.05)",
                  border: isDone
                    ? "1px solid rgba(179,158,244,0.5)"
                    : isActive
                    ? "1px solid #8b6fe8"
                    : "1px solid rgba(255,255,255,0.1)",
                  color: isDone ? "white" : isActive ? "#b39ef4" : "rgba(250,248,242,0.3)",
                  boxShadow: isActive ? "0 0 16px rgba(99,71,212,0.4)" : "none",
                }}
              >
                {isDone ? (
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path d="M2 7l3.5 3.5L12 3.5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                ) : (
                  step.number
                )}
              </div>
              <span
                className="text-xs whitespace-nowrap hidden sm:block"
                style={{
                  color: isActive
                    ? "var(--purple-300)"
                    : isDone
                    ? "rgba(250,248,242,0.5)"
                    : "rgba(250,248,242,0.2)",
                  fontWeight: isActive ? 500 : 400,
                }}
              >
                {step.label}
              </span>
            </div>

            {/* Connector */}
            {i < STEPS.length - 1 && (
              <div
                className="w-16 sm:w-24 h-px mx-2 mb-5 transition-all duration-500"
                style={{
                  background: isDone
                    ? "linear-gradient(90deg, #6347d4, #8b6fe8)"
                    : "rgba(255,255,255,0.08)",
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
