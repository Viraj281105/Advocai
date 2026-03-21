"use client";
import { FileText, User, Building2, Stethoscope, Calendar, MessageSquare, CheckCircle } from "lucide-react";
import type { CaseDetails } from "./CaseDetailsForm";

interface Props {
  denialFile: File | null;
  policyFile: File | null;
  details: CaseDetails;
}

function ReviewRow({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div
      className="flex items-start gap-4 py-4"
      style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
    >
      <div
        className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
        style={{ background: "rgba(99,71,212,0.12)" }}
      >
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs mb-1" style={{ color: "rgba(250,248,242,0.4)" }}>
          {label}
        </p>
        <p
          className="text-sm font-medium truncate"
          style={{ color: value ? "var(--cream)" : "rgba(250,248,242,0.25)" }}
        >
          {value || "—"}
        </p>
      </div>
    </div>
  );
}

function FileRow({ label, file }: { label: string; file: File | null }) {
  const formatSize = (bytes: number) => `${(bytes / (1024 * 1024)).toFixed(1)} MB`;

  return (
    <div
      className="flex items-center gap-4 py-4"
      style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
    >
      <div
        className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
        style={{
          background: file ? "rgba(52,211,153,0.1)" : "rgba(255,255,255,0.04)",
        }}
      >
        {file ? (
          <CheckCircle size={16} color="#34d399" />
        ) : (
          <FileText size={16} color="rgba(250,248,242,0.3)" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs mb-1" style={{ color: "rgba(250,248,242,0.4)" }}>
          {label}
        </p>
        <p
          className="text-sm font-medium truncate"
          style={{ color: file ? "var(--cream)" : "rgba(250,248,242,0.25)" }}
        >
          {file ? `${file.name} (${formatSize(file.size)})` : "Not uploaded"}
        </p>
      </div>
    </div>
  );
}

export default function ReviewPanel({ denialFile, policyFile, details }: Props) {
  return (
    <div className="flex flex-col gap-6">
      {/* Files section */}
      <div
        className="rounded-2xl p-6"
        style={{
          background: "rgba(255,255,255,0.02)",
          border: "1px solid rgba(255,255,255,0.07)",
        }}
      >
        <p
          className="text-xs uppercase tracking-widest font-medium mb-2"
          style={{ color: "var(--purple-400)" }}
        >
          Documents
        </p>
        <FileRow label="Denial letter" file={denialFile} />
        <FileRow label="Insurance policy" file={policyFile} />
      </div>

      {/* Case details section */}
      <div
        className="rounded-2xl p-6"
        style={{
          background: "rgba(255,255,255,0.02)",
          border: "1px solid rgba(255,255,255,0.07)",
        }}
      >
        <p
          className="text-xs uppercase tracking-widest font-medium mb-2"
          style={{ color: "var(--purple-400)" }}
        >
          Case details
        </p>
        <ReviewRow
          icon={<User size={15} color="#8b6fe8" />}
          label="Patient name"
          value={details.patientName}
        />
        <ReviewRow
          icon={<Building2 size={15} color="#8b6fe8" />}
          label="Insurance company"
          value={details.insurerName}
        />
        <ReviewRow
          icon={<Stethoscope size={15} color="#8b6fe8" />}
          label="Procedure denied"
          value={details.procedureDenied}
        />
        <ReviewRow
          icon={<Calendar size={15} color="#8b6fe8" />}
          label="Date of denial"
          value={details.denialDate}
        />
        {details.notes && (
          <ReviewRow
            icon={<MessageSquare size={15} color="#8b6fe8" />}
            label="Additional context"
            value={details.notes}
          />
        )}
      </div>

      {/* What happens next */}
      <div
        className="rounded-2xl p-6"
        style={{
          background: "linear-gradient(135deg, rgba(79,49,184,0.12), rgba(99,71,212,0.06))",
          border: "1px solid rgba(179,158,244,0.15)",
        }}
      >
        <p
          className="text-xs uppercase tracking-widest font-medium mb-4"
          style={{ color: "var(--purple-400)" }}
        >
          What happens next
        </p>
        <div className="flex flex-col gap-3">
          {[
            { agent: "Auditor", task: "Parses your PDFs and extracts denial codes", time: "~2s" },
            { agent: "Clinician", task: "Finds PubMed evidence supporting your case", time: "~8s" },
            { agent: "Regulatory", task: "Identifies ACA & ERISA statutes in your favor", time: "~3s" },
            { agent: "Barrister", task: "Drafts your full appeal letter", time: "~4s" },
            { agent: "Judge", task: "Scores and validates the final output", time: "~2s" },
          ].map((item) => (
            <div key={item.agent} className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div
                  className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                  style={{ background: "var(--purple-400)" }}
                />
                <span className="text-sm" style={{ color: "rgba(250,248,242,0.6)" }}>
                  <span style={{ color: "var(--cream)", fontWeight: 500 }}>{item.agent}</span>{" "}
                  — {item.task}
                </span>
              </div>
              <span
                className="text-xs flex-shrink-0"
                style={{ color: "rgba(250,248,242,0.3)" }}
              >
                {item.time}
              </span>
            </div>
          ))}
        </div>
        <p
          className="text-xs mt-5 pt-4"
          style={{
            color: "rgba(250,248,242,0.3)",
            borderTop: "1px solid rgba(255,255,255,0.06)",
          }}
        >
          Total estimated time: ~20 seconds · No PHI is stored or logged
        </p>
      </div>
    </div>
  );
}
