// frontend/middleware.ts
// Issue #9 — Redirect unauthenticated users to /login
// Next.js Edge Middleware — runs before every request

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Routes that don't require authentication
const PUBLIC_PATHS = new Set(["/login", "/register", "/", "/api/auth/login", "/api/auth/register"]);

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public paths and Next.js internals
  if (
    PUBLIC_PATHS.has(pathname) ||
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon")
  ) {
    return NextResponse.next();
  }

  // Read JWT from httpOnly cookie
  const token = request.cookies.get("advocai_token")?.value;

  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Token exists — allow through (backend validates on each API call)
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
