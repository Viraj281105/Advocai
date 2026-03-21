"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { Scale } from "lucide-react";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav style={{
      position: "fixed", top: 0, left: 0, right: 0, zIndex: 50,
      transition: "all 0.5s ease",
      background: scrolled ? "rgba(15,10,30,0.85)" : "transparent",
      backdropFilter: scrolled ? "blur(16px)" : "none",
      borderBottom: scrolled ? "1px solid rgba(255,255,255,0.07)" : "1px solid transparent",
    }}>
      <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "1rem 1.5rem", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <Link href="/" style={{ display: "flex", alignItems: "center", gap: "0.5rem", textDecoration: "none" }}>
          <div style={{ width: "2rem", height: "2rem", borderRadius: "0.5rem", display: "flex", alignItems: "center", justifyContent: "center", background: "linear-gradient(135deg, #4f31b8, #8b6fe8)" }}>
            <Scale size={16} color="white" />
          </div>
          <span style={{ fontFamily: "var(--font-display)", fontSize: "1.25rem", letterSpacing: "-0.01em", color: "var(--cream)" }}>
            Advoc<span className="gold-text">AI</span>
          </span>
        </Link>

        <div style={{ display: "flex", alignItems: "center", gap: "2rem" }}>
          {[{ label: "How it works", href: "#how-it-works" }, { label: "The agents", href: "#agents" }, { label: "Impact", href: "#impact" }].map(link => (
            <a key={link.href} href={link.href} style={{ fontSize: "0.875rem", color: "rgba(250,248,242,0.6)", textDecoration: "none", transition: "color 0.2s" }}
              onMouseEnter={e => (e.currentTarget.style.color = "var(--cream)")}
              onMouseLeave={e => (e.currentTarget.style.color = "rgba(250,248,242,0.6)")}>
              {link.label}
            </a>
          ))}
        </div>

        <Link href="/submit" className="btn-primary" style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.5rem 1.25rem", borderRadius: "9999px", fontSize: "0.875rem", fontWeight: 500, color: "white", textDecoration: "none" }}>
          <span>Start your appeal</span>
          <span style={{ color: "var(--gold-light)" }}>→</span>
        </Link>
      </div>
    </nav>
  );
}
