"use client";
// frontend/components/CaseTable.tsx
// Issue #10 — Card grid: Case ID, procedure denied, date, status badge, actions

import { useRouter } from "next/navigation";
import type { AppealCase, CaseStatus } from "@/app/dashboard/page";

// ── Status badge ──────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<CaseStatus, { label: string; classes: string }> = {
  completed: {
    label: "Completed",
    classes: "bg-green-100 text-green-700 border border-green-200",
  },
  in_progress: {
    label: "In Progress",
    classes: "bg-amber-100 text-amber-700 border border-amber-200",
  },
  failed: {
    label: "Failed",
    classes: "bg-red-100 text-red-700 border border-red-200",
  },
};

function StatusBadge({ status }: { status: CaseStatus }) {
  const { label, classes } = STATUS_CONFIG[status];
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${classes}`}>
      {label}
    </span>
  );
}

// ── CaseCard ──────────────────────────────────────────────────────────────

function CaseCard({ c }: { c: AppealCase }) {
  const router = useRouter();
  const date = new Date(c.created_at).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col gap-4 hover:shadow-md transition-shadow">
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs text-slate-400 font-mono mb-1">#{c.id.slice(0, 8)}</p>
          <h3 className="text-sm font-semibold text-slate-800 truncate" title={c.procedure_denied}>
            {c.procedure_denied}
          </h3>
        </div>
        <StatusBadge status={c.status} />
      </div>

      {/* Date */}
      <p className="text-xs text-slate-500">{date}</p>

      {/* Action buttons */}
      <div className="flex gap-2 mt-auto">
        {c.status === "completed" && (
          <button
            onClick={() => router.push(`/case/${c.id}`)}
            className="flex-1 rounded-lg border border-slate-300 hover:bg-slate-50 px-3 py-2 text-xs font-medium text-slate-700 transition-colors"
          >
            View
          </button>
        )}

        {c.status === "in_progress" && c.has_checkpoint && (
          <button
            onClick={() => router.push(`/case/${c.id}/resume`)}
            className="flex-1 rounded-lg bg-blue-600 hover:bg-blue-700 px-3 py-2 text-xs font-semibold text-white transition-colors"
          >
            Resume
          </button>
        )}

        {c.status === "failed" && (
          <button
            onClick={() => router.push(`/case/${c.id}/retry`)}
            className="flex-1 rounded-lg border border-red-300 hover:bg-red-50 px-3 py-2 text-xs font-medium text-red-600 transition-colors"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}

// ── CaseTable (grid of cards) ─────────────────────────────────────────────

interface CaseTableProps {
  cases: AppealCase[];
}

export default function CaseTable({ cases }: CaseTableProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {cases.map((c) => (
        <CaseCard key={c.id} c={c} />
      ))}
    </div>
  );
}
