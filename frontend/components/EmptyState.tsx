"use client";
// frontend/components/EmptyState.tsx
// Issue #10 — Empty state for first-time users

import { useRouter } from "next/navigation";

export default function EmptyState() {
  const router = useRouter();

  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-200 bg-white px-8 py-20 text-center">
      {/* Icon */}
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-blue-50">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-8 w-8 text-blue-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M9 12h3.75M9 15h3.75M9 18h3.75m3-10.5H18a2.25 2.25 0 012.25 2.25V19.5A2.25 2.25 0 0118 21.75H6A2.25 2.25 0 013.75 19.5V8.25A2.25 2.25 0 016 6h2.25m0 0V4.875A2.625 2.625 0 0110.875 2.25h.375a2.625 2.625 0 012.625 2.625V6m-6.75 0h6.75"
          />
        </svg>
      </div>

      <h3 className="text-lg font-semibold text-slate-800 mb-1">No cases yet</h3>
      <p className="text-sm text-slate-500 max-w-sm mb-6">
        Start your first insurance appeal. AdvocAI will handle the medical evidence, legal
        arguments, and letter writing — automatically.
      </p>

      <button
        onClick={() => router.push("/case/new")}
        className="rounded-lg bg-blue-600 hover:bg-blue-700 px-6 py-2.5 text-sm font-semibold text-white transition-colors"
      >
        Start your first appeal →
      </button>
    </div>
  );
}
