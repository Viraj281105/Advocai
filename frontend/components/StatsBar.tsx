"use client";
import { useEffect, useRef, useState } from "react";

const STATS = [
  { value: 67, suffix: "%", label: "of denied claims are never appealed" },
  { value: 45, suffix: "%", label: "of appealed claims are overturned" },
  { value: 5,  suffix: "",  label: "specialized AI agents on your side" },
  { value: 30, suffix: "s", label: "to generate your full appeal letter" },
];

function AnimatedNumber({ target, suffix }: { target: number; suffix: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const started = useRef(false);
  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting && !started.current) {
        started.current = true;
        const steps = 60;
        const increment = target / steps;
        let current = 0;
        const timer = setInterval(() => {
          current += increment;
          if (current >= target) { setCount(target); clearInterval(timer); }
          else setCount(Math.floor(current));
        }, 1800 / steps);
      }
    }, { threshold: 0.5 });
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [target]);
  return <span ref={ref}>{count}{suffix}</span>;
}

export default function StatsBar() {
  return (
    <section id="impact" style={{ position: "relative", padding: "6rem 1.5rem" }}>
      <div className="divider" style={{ marginBottom: "6rem" }} />
      <div style={{ maxWidth: "1280px", margin: "0 auto" }}>
        <p style={{ textAlign: "center", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.15em", color: "var(--purple-400)", fontWeight: 500, marginBottom: "4rem" }}>
          The gap AdvocAI closes
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1.5rem" }}>
          {STATS.map((stat, i) => (
            <div key={i} style={{ background: "rgba(255,255,255,0.03)", backdropFilter: "blur(12px)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "1rem", padding: "2rem", textAlign: "center", transition: "background 0.3s, border-color 0.3s, transform 0.3s" }}
              onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.background = "rgba(255,255,255,0.06)"; (e.currentTarget as HTMLDivElement).style.transform = "translateY(-2px)"; }}
              onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.background = "rgba(255,255,255,0.03)"; (e.currentTarget as HTMLDivElement).style.transform = "translateY(0)"; }}>
              <div className="gradient-text" style={{ fontFamily: "var(--font-display)", fontSize: "clamp(2.5rem, 5vw, 3.5rem)", lineHeight: 1, marginBottom: "0.75rem" }}>
                <AnimatedNumber target={stat.value} suffix={stat.suffix} />
              </div>
              <p style={{ fontSize: "0.875rem", lineHeight: 1.6, color: "rgba(250,248,242,0.5)" }}>{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
      <div className="divider" style={{ marginTop: "6rem" }} />
    </section>
  );
}
