// frontend/app/api/cases/route.ts
// Proxies GET /api/cases to the FastAPI backend, forwarding the JWT cookie as Bearer

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET(req: NextRequest) {
  const token = req.cookies.get("advocai_token")?.value;

  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const upstream = await fetch(`${BACKEND_URL}/api/cases`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await upstream.json().catch(() => []);
  return NextResponse.json(data, { status: upstream.status });
}
