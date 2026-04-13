"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ArrowRight, Loader2, Scale } from "lucide-react";
import StepIndicator from "@/components/submit/StepIndicator";
import FileDropzone from "@/components/submit/FileDropzone";
import CaseDetailsForm, { type CaseDetails } from "@/components/submit/CaseDetailsForm";
import ReviewPanel from "@/components/submit/ReviewPanel";

const EMPTY_DETAILS: CaseDetails = {
  patientName: "", insurerName: "", procedureDenied: "", denialDate: "", notes: "",
};

type FormErrors = Partial<Record<keyof CaseDetails, string>>;

const STEP_TITLES = [
  { title: "Upload your denial letter",   sub: "Drop in the PDF your insurer sent you." },
  { title: "Upload your policy document", sub: "The insurance policy PDF for your plan." },
  { title: "Tell us about your case",     sub: "A few details so our agents can tailor the appeal." },
  { title: "Review and submit",           sub: "Double-check everything before the agents go to work." },
];

export default function SubmitPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [denialFile, setDenialFile] = useState<File | null>(null);
  const [policyFile, setPolicyFile] = useState<File | null>(null);
  const [details, setDetails] = useState<CaseDetails>(EMPTY_DETAILS);
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);

  const validate = (): boolean => {
    if (step === 1 && !denialFile) { alert("Please upload your denial letter PDF."); return false; }
    if (step === 2 && !policyFile) { alert("Please upload your policy document PDF."); return false; }
    if (step === 3) {
      const e: FormErrors = {};
      if (!details.patientName.trim() || details.patientName.trim().length < 2) e.patientName = "At least 2 characters required.";
      if (!details.insurerName.trim()) e.insurerName = "Insurance company name is required.";
      if (!details.procedureDenied.trim()) e.procedureDenied = "Please specify the procedure denied.";
      setErrors(e);
      return Object.keys(e).length === 0;
    }
    return true;
  };

  
  const next = () => { if (validate()) setStep(s => Math.min(s + 1, 4)); };
  const back = () => { setErrors({}); setStep(s => Math.max(s - 1, 1)); };

  const submit = async () => {
    setSubmitting(true);
    try {
      const formData = new FormData();
      if (denialFile) formData.append("denial_pdf", denialFile);
      if (policyFile) formData.append("policy_pdf", policyFile);
      formData.append("patient_name", details.patientName);
      formData.append("insurer_name", details.insurerName);
      formData.append("procedure_denied", details.procedureDenied);
      formData.append("denial_date", details.denialDate);
      formData.append("notes", details.notes);

      let sessionId = "demo_" + Date.now();
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/submit`, { method: "POST", body: formData });
        if (res.ok) { const d = await res.json(); sessionId = d.session_id || sessionId; }
      } catch {
        await new Promise(r => setTimeout(r, 1200));
      }
      router.push(`/case/${sessionId}`);
    } catch (err) {
      console.error(err);
      setSubmitting(false);
    }
  };

  const { title, sub } = STEP_TITLES[step - 1];

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", background: "var(--purple-950)", position: "relative" }}>
      <div className="orb orb-1" style={{ position: "fixed", opacity: 0.5 }} />
      <div className="orb orb-2" style={{ position: "fixed", opacity: 0.4 }} />

      {/* Header */}
      <header style={{ position: "relative", zIndex: 10, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1.25rem 1.5rem", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <Link href="/" style={{ display: "flex", alignItems: "center", gap: "0.5rem", textDecoration: "none" }}>
          <div style={{ width: "1.75rem", height: "1.75rem", borderRadius: "0.5rem", display: "flex", alignItems: "center", justifyContent: "center", background: "linear-gradient(135deg, #4f31b8, #8b6fe8)" }}>
            <Scale size={14} color="white" />
          </div>
          <span style={{ fontFamily: "var(--font-display)", fontSize: "1.1rem", color: "var(--cream)" }}>
            Advoc<span className="gold-text">AI</span>
          </span>
        </Link>
        <span style={{ fontSize: "0.8rem", color: "rgba(250,248,242,0.3)" }}>Step {step} of 4</span>
      </header>

      {/* Main */}
      <main style={{ position: "relative", zIndex: 10, flex: 1, display: "flex", alignItems: "flex-start", justifyContent: "center", padding: "clamp(1.5rem, 5vw, 3rem) 1rem 4rem" }}>
        <div style={{ width: "100%", maxWidth: "680px" }}>
          <StepIndicator currentStep={step} />

          {/* Card */}
          <div style={{ borderRadius: "1.5rem", padding: "clamp(1.25rem, 5vw, 2.5rem)", background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)", backdropFilter: "blur(12px)" }}>
            <div style={{ marginBottom: "1.5rem" }}>
              <h1 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(1.4rem, 4vw, 2.2rem)", lineHeight: 1.15, letterSpacing: "-0.01em", marginBottom: "0.5rem", color: "var(--cream)" }}>
                {title}
              </h1>
              <p style={{ fontSize: "0.875rem", color: "rgba(250,248,242,0.45)" }}>{sub}</p>
            </div>

            <div style={{ marginBottom: "1.5rem" }}>
              {step === 1 && <FileDropzone label="Drag & drop your denial letter" description="The letter your insurance company sent denying your claim" file={denialFile} onFile={setDenialFile} />}
              {step === 2 && <FileDropzone label="Drag & drop your policy document" description="Your insurance plan's policy PDF — usually from your insurer's member portal" file={policyFile} onFile={setPolicyFile} />}
              {step === 3 && <CaseDetailsForm values={details} onChange={setDetails} errors={errors} />}
              {step === 4 && <ReviewPanel denialFile={denialFile} policyFile={policyFile} details={details} />}
            </div>

            {/* Navigation */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.75rem", paddingTop: "1.25rem", borderTop: "1px solid rgba(255,255,255,0.06)" }}>
              {step > 1 ? (
                <button onClick={back} className="btn-secondary" style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.75rem 1.25rem", borderRadius: "9999px", fontSize: "0.875rem", fontWeight: 500, color: "rgba(250,248,242,0.6)", cursor: "pointer" }}>
                  <ArrowLeft size={15} /> Back
                </button>
              ) : (
                <Link href="/" className="btn-secondary" style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.75rem 1.25rem", borderRadius: "9999px", fontSize: "0.875rem", fontWeight: 500, color: "rgba(250,248,242,0.6)", textDecoration: "none" }}>
                  <ArrowLeft size={15} /> Home
                </Link>
              )}
              {step < 4 ? (
                <button onClick={next} className="btn-primary" style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.75rem 1.5rem", borderRadius: "9999px", fontSize: "0.875rem", fontWeight: 500, color: "white", cursor: "pointer" }}>
                  <span>Continue</span><ArrowRight size={15} />
                </button>
              ) : (
                <button onClick={submit} disabled={submitting} className="btn-primary" style={{ display: "inline-flex", alignItems: "center", gap: "0.75rem", padding: "0.75rem 1.75rem", borderRadius: "9999px", fontSize: "0.875rem", fontWeight: 500, color: "white", cursor: submitting ? "not-allowed" : "pointer", opacity: submitting ? 0.6 : 1 }}>
                  {submitting ? <><Loader2 size={16} style={{ animation: "spin 1s linear infinite" }} /><span>Launching agents...</span></> : <><span>Submit appeal</span><ArrowRight size={15} /></>}
                </button>
              )}
            </div>
          </div>

          <p style={{ textAlign: "center", fontSize: "0.75rem", marginTop: "1.25rem", color: "rgba(250,248,242,0.2)" }}>
            Your files are processed locally and never stored. MIT licensed · Open source.
          </p>
        </div>
      </main>

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}