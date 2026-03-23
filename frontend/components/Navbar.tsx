"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { Scale, Menu, X } from "lucide-react";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav style={{
      position: "fixed", top: 0, left: 0, right: 0, zIndex: 50,
      transition: "all 0.5s ease",
      background: scrolled || menuOpen ? "rgba(15,10,30,0.95)" : "transparent",
      backdropFilter: scrolled || menuOpen ? "blur(16px)" : "none",
      borderBottom: scrolled || menuOpen ? "1px solid rgba(255,255,255,0.07)" : "1px solid transparent",
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

        {/* Desktop links */}
        <div style={{ display: "flex", alignItems: "center", gap: "2rem" }} className="desktop-nav">
          {[{ label: "How it works", href: "#how-it-works" }, { label: "The agents", href: "#agents" }, { label: "Impact", href: "#impact" }].map(link => (
            <a key={link.href} href={link.href} style={{ fontSize: "0.875rem", color: "rgba(250,248,242,0.6)", textDecoration: "none", transition: "color 0.2s" }}
              onMouseEnter={e => (e.currentTarget.style.color = "var(--cream)")}
              onMouseLeave={e => (e.currentTarget.style.color = "rgba(250,248,242,0.6)")}>
              {link.label}
            </a>
          ))}
          <Link href="/submit" className="btn-primary" style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.5rem 1.25rem", borderRadius: "9999px", fontSize: "0.875rem", fontWeight: 500, color: "white", textDecoration: "none" }}>
            <span>Start your appeal</span>
            <span style={{ color: "var(--gold-light)" }}>→</span>
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button onClick={() => setMenuOpen(o => !o)} className="mobile-nav-btn" style={{ background: "none", border: "none", cursor: "pointer", color: "var(--cream)", padding: "4px" }}>
          {menuOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div style={{ padding: "1rem 1.5rem 1.5rem", borderTop: "1px solid rgba(255,255,255,0.07)", display: "flex", flexDirection: "column", gap: "1rem" }}>
          {[{ label: "How it works", href: "#how-it-works" }, { label: "The agents", href: "#agents" }, { label: "Impact", href: "#impact" }].map(link => (
            <a key={link.href} href={link.href} onClick={() => setMenuOpen(false)}
              style={{ fontSize: "1rem", color: "rgba(250,248,242,0.7)", textDecoration: "none", padding: "0.5rem 0" }}>
              {link.label}
            </a>
          ))}
          <Link href="/submit" onClick={() => setMenuOpen(false)} className="btn-primary"
            style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", padding: "0.875rem", borderRadius: "9999px", fontSize: "0.95rem", fontWeight: 500, color: "white", textDecoration: "none", marginTop: "0.5rem" }}>
            <span>Start your appeal</span>
            <span style={{ color: "var(--gold-light)" }}>→</span>
          </Link>
        </div>
      )}

      <style>{`
        @media (min-width: 768px) { .mobile-nav-btn { display: none !important; } }
        @media (max-width: 767px) { .desktop-nav { display: none !important; } }
      `}</style>
    </nav>
  );
}