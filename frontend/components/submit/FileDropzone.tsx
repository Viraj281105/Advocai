"use client";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { FileText, Upload, X, CheckCircle } from "lucide-react";

interface Props {
  label: string;
  description: string;
  file: File | null;
  onFile: (file: File | null) => void;
}

export default function FileDropzone({ label, description, file, onFile }: Props) {
  const [dragOver, setDragOver] = useState(false);

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) onFile(accepted[0]);
    setDragOver(false);
  }, [onFile]);

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "image/jpeg": [".jpg", ".jpeg"], "image/png": [".png"] },
    maxSize: 10 * 1024 * 1024,
    multiple: false,
    onDragEnter: () => setDragOver(true),
    onDragLeave: () => setDragOver(false),
  });

  const formatSize = (bytes: number) => `${(bytes / (1024 * 1024)).toFixed(1)} MB`;

  if (file) {
    return (
      <div style={{
        borderRadius: "1rem",
        padding: "1.5rem",
        display: "flex",
        alignItems: "center",
        gap: "1rem",
        background: "rgba(52,211,153,0.05)",
        border: "1px solid rgba(52,211,153,0.3)",
        transition: "all 0.3s ease",
      }}>
        <div style={{ width: "3rem", height: "3rem", borderRadius: "0.75rem", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, background: "rgba(52,211,153,0.1)" }}>
          <CheckCircle size={22} color="#34d399" />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{ fontWeight: 500, fontSize: "0.9rem", color: "#faf8f2", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{file.name}</p>
          <p style={{ fontSize: "0.75rem", marginTop: "3px", color: "rgba(250,248,242,0.4)" }}>{formatSize(file.size)} · Document · Ready</p>
        </div>
        <button
          onClick={() => onFile(null)}
          style={{ width: "2rem", height: "2rem", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, background: "transparent", border: "1px solid rgba(255,255,255,0.1)", cursor: "pointer", transition: "background 0.2s" }}
          onMouseEnter={e => (e.currentTarget.style.background = "rgba(248,113,113,0.2)")}
          onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
        >
          <X size={14} color="rgba(250,248,242,0.5)" />
        </button>
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      style={{
        borderRadius: "1rem",
        padding: "4rem 2rem",
        textAlign: "center",
        cursor: "pointer",
        transition: "all 0.3s ease",
        background: dragOver ? "rgba(99,71,212,0.12)" : "rgba(255,255,255,0.02)",
        border: dragOver ? "2px dashed rgba(179,158,244,0.7)" : "2px dashed rgba(255,255,255,0.12)",
        transform: dragOver ? "scale(1.01)" : "scale(1)",
      }}
    >
      <input {...getInputProps()} />

      {/* Icon */}
      <div style={{
        width: "5rem",
        height: "5rem",
        borderRadius: "1.25rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        margin: "0 auto 1.5rem",
        background: dragOver ? "rgba(99,71,212,0.2)" : "rgba(255,255,255,0.04)",
        border: "1px solid rgba(255,255,255,0.08)",
        transition: "all 0.3s ease",
      }}>
        {dragOver
          ? <FileText size={32} color="#8b6fe8" />
          : <Upload size={32} color="rgba(250,248,242,0.3)" />
        }
      </div>

      {/* Text */}
      <p style={{ fontSize: "1.05rem", fontWeight: 500, marginBottom: "0.5rem", color: dragOver ? "#b39ef4" : "#faf8f2", transition: "color 0.3s" }}>
        {label}
      </p>
      <p style={{ fontSize: "0.875rem", marginBottom: "2rem", color: "rgba(250,248,242,0.4)", lineHeight: 1.6 }}>
        {description}
      </p>

      {/* Button */}
      <div style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.5rem",
        padding: "0.625rem 1.5rem",
        borderRadius: "9999px",
        fontSize: "0.875rem",
        fontWeight: 500,
        background: "rgba(99,71,212,0.15)",
        border: "1px solid rgba(179,158,244,0.25)",
        color: "#b39ef4",
        transition: "all 0.2s ease",
      }}>
        <FileText size={15} />
        Browse Files
      </div>

      <p style={{ fontSize: "0.75rem", marginTop: "1.5rem", color: "rgba(250,248,242,0.2)" }}>
        PDF, JPG, PNG · Max 10 MB
      </p>
    </div>
  );
}
