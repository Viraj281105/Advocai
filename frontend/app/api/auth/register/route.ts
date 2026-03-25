// frontend/app/api/auth/register/route.ts
// Proxies registration to FastAPI backend; sets the JWT as an httpOnly cookie

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest) {
  const body = await req.json();

  const upstream = await fetch(`${BACKEND_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!upstream.ok) {
    const err = await upstream.json().catch(() => ({ detail: "Registration failed" }));
    return NextResponse.json(err, { status: upstream.status });
  }

  const { access_token } = await upstream.json();

  const response = NextResponse.json({ ok: true }, { status: 201 });
  response.cookies.set("advocai_token", access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24,
  });
  return response;
}
