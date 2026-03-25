"use client";
// frontend/app/dashboard/page.tsx
// Issue #10 — Case history dashboard: list all past cases with status + resume

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import CaseTable from "@/components/CaseTable";
import EmptyState from "@/components/EmptyState";

export type CaseStatus = "completed" | "in_progress" | "failed";

export interface AppealCase {
  id: string;
  procedure_denied: string;
  created_at: string; // ISO string
  updated_at: string;
  status: CaseStatus;
  has_checkpoint: boolean;
}

export default function DashboardPage() {
  const router = useRouter();
  const [cases, setCases] = useState<AppealCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchCases() {
      try {
        const res = await fetch("/api/cases");
        if (res.status === 401) {
          router.push("/login");
          return;
        }
        if (!res.ok) throw new Error("Failed to load cases");
        const data: AppealCase[] = await res.json();
        setCases(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }
    fetchCases();
  }, [router]);

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Navbar */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <span className="text-xl font-bold text-slate-800">AdvocAI</span>
        <nav className="flex items-center gap-4">
          <button
            onClick={() => router.push("/case/new")}
            className="rounded-lg bg-blue-600 hover:bg-blue-700 px-4 py-2 text-sm font-semibold text-white transition-colors"
          >
            + New Case
          </button>
          <button
            onClick={handleLogout}
            className="text-sm text-slate-500 hover:text-slate-800 transition-colors"
          >
            Sign out
          </button>
        </nav>
      </header>

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-6 py-10">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-800">Your Cases</h2>
          <p className="mt-1 text-slate-500 text-sm">
            All your insurance appeal cases — view completed ones or resume in-progress work.
          </p>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-24">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600" />
          </div>
        )}

        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {!loading && !error && cases.length === 0 && <EmptyState />}

        {!loading && !error && cases.length > 0 && <CaseTable cases={cases} />}
      </main>
    </div>
  );
}
