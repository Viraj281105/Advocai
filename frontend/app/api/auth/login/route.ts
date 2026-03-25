// frontend/app/api/auth/login/route.ts
// Proxies login to FastAPI backend; sets the JWT as an httpOnly cookie

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest) {
  const { email, password } = await req.json();

  // FastAPI expects OAuth2 form fields
  const form = new URLSearchParams();
  form.append("username", email); // OAuth2PasswordRequestForm uses 'username'
  form.append("password", password);

  const upstream = await fetch(`${BACKEND_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });

  if (!upstream.ok) {
    const err = await upstream.json().catch(() => ({ detail: "Login failed" }));
    return NextResponse.json(err, { status: upstream.status });
  }

  const { access_token } = await upstream.json();

  const response = NextResponse.json({ ok: true }, { status: 200 });
  response.cookies.set("advocai_token", access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24, // 24 hours
  });
  return response;
}
