"use client";

export interface CaseDetails {
  patientName: string;
  insurerName: string;
  procedureDenied: string;
  denialDate: string;
  notes: string;
}

interface Props {
  values: CaseDetails;
  onChange: (values: CaseDetails) => void;
  errors: Partial<Record<keyof CaseDetails, string>>;
}

const inputStyle = {
  width: "100%",
  background: "rgba(255,255,255,0.04)",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: "12px",
  padding: "14px 16px",
  color: "var(--cream)",
  fontSize: "15px",
  outline: "none",
  transition: "border-color 0.2s ease, box-shadow 0.2s ease",
  fontFamily: "var(--font-body)",
};

const labelStyle = {
  display: "block",
  fontSize: "13px",
  fontWeight: 500,
  marginBottom: "8px",
  color: "rgba(250,248,242,0.6)",
};

const errorStyle = {
  fontSize: "12px",
  color: "#f87171",
  marginTop: "5px",
};

export default function CaseDetailsForm({ values, onChange, errors }: Props) {
  const set = (key: keyof CaseDetails) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => onChange({ ...values, [key]: e.target.value });

  const focusStyle = (hasError: boolean) => ({
    ...inputStyle,
    borderColor: hasError ? "rgba(248,113,113,0.5)" : undefined,
  });

  return (
    <div className="flex flex-col gap-5">
      {/* Row 1 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div>
          <label style={labelStyle}>
            Patient name <span style={{ color: "#f87171" }}>*</span>
          </label>
          <input
            type="text"
            placeholder="Full name"
            value={values.patientName}
            onChange={set("patientName")}
            style={focusStyle(!!errors.patientName)}
            onFocus={(e) => {
              e.target.style.borderColor = "rgba(179,158,244,0.5)";
              e.target.style.boxShadow = "0 0 0 3px rgba(99,71,212,0.15)";
            }}
            onBlur={(e) => {
              e.target.style.borderColor = errors.patientName
                ? "rgba(248,113,113,0.5)"
                : "rgba(255,255,255,0.1)";
              e.target.style.boxShadow = "none";
            }}
          />
          {errors.patientName && <p style={errorStyle}>{errors.patientName}</p>}
        </div>

        <div>
          <label style={labelStyle}>
            Insurance company <span style={{ color: "#f87171" }}>*</span>
          </label>
          <input
            type="text"
            placeholder="e.g. Blue Cross, Aetna, UnitedHealth"
            value={values.insurerName}
            onChange={set("insurerName")}
            style={focusStyle(!!errors.insurerName)}
            onFocus={(e) => {
              e.target.style.borderColor = "rgba(179,158,244,0.5)";
              e.target.style.boxShadow = "0 0 0 3px rgba(99,71,212,0.15)";
            }}
            onBlur={(e) => {
              e.target.style.borderColor = errors.insurerName
                ? "rgba(248,113,113,0.5)"
                : "rgba(255,255,255,0.1)";
              e.target.style.boxShadow = "none";
            }}
          />
          {errors.insurerName && <p style={errorStyle}>{errors.insurerName}</p>}
        </div>
      </div>

      {/* Row 2 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div>
          <label style={labelStyle}>
            Procedure / treatment denied <span style={{ color: "#f87171" }}>*</span>
          </label>
          <input
            type="text"
            placeholder="e.g. Genomic sequencing, MRI, Infusion therapy"
            value={values.procedureDenied}
            onChange={set("procedureDenied")}
            style={focusStyle(!!errors.procedureDenied)}
            onFocus={(e) => {
              e.target.style.borderColor = "rgba(179,158,244,0.5)";
              e.target.style.boxShadow = "0 0 0 3px rgba(99,71,212,0.15)";
            }}
            onBlur={(e) => {
              e.target.style.borderColor = errors.procedureDenied
                ? "rgba(248,113,113,0.5)"
                : "rgba(255,255,255,0.1)";
              e.target.style.boxShadow = "none";
            }}
          />
          {errors.procedureDenied && <p style={errorStyle}>{errors.procedureDenied}</p>}
        </div>

        <div>
          <label style={labelStyle}>Date of denial</label>
          <input
            type="date"
            value={values.denialDate}
            onChange={set("denialDate")}
            style={{
              ...inputStyle,
              colorScheme: "dark",
            }}
            onFocus={(e) => {
              e.target.style.borderColor = "rgba(179,158,244,0.5)";
              e.target.style.boxShadow = "0 0 0 3px rgba(99,71,212,0.15)";
            }}
            onBlur={(e) => {
              e.target.style.borderColor = "rgba(255,255,255,0.1)";
              e.target.style.boxShadow = "none";
            }}
          />
        </div>
      </div>

      {/* Notes */}
      <div>
        <label style={labelStyle}>Additional context (optional)</label>
        <textarea
          rows={4}
          placeholder="Any extra context that might help: prior authorizations, doctor's notes, previous appeal attempts..."
          value={values.notes}
          onChange={set("notes")}
          style={{ ...inputStyle, resize: "vertical", lineHeight: 1.6 }}
          onFocus={(e) => {
            e.target.style.borderColor = "rgba(179,158,244,0.5)";
            e.target.style.boxShadow = "0 0 0 3px rgba(99,71,212,0.15)";
          }}
          onBlur={(e) => {
            e.target.style.borderColor = "rgba(255,255,255,0.1)";
            e.target.style.boxShadow = "none";
          }}
        />
      </div>
    </div>
  );
}
