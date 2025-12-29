import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Public routes that don't require authentication
const publicRoutes = ["/login"];

// Routes that pending users can access
const pendingAllowedRoutes = ["/pending", "/login"];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip API routes and static files
  if (
    pathname.startsWith("/api") ||
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // Check for access token cookie
  const accessToken = request.cookies.get("access_token")?.value;

  // Public routes - allow access without auth
  if (publicRoutes.includes(pathname)) {
    // If already logged in, redirect to home
    if (accessToken) {
      return NextResponse.redirect(new URL("/", request.url));
    }
    return NextResponse.next();
  }

  // No token - redirect to login
  if (!accessToken) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  // For authenticated users, we need to check their status
  // We'll do this by calling the backend API
  try {
    const response = await fetch(`${getBackendUrl(request)}/api/v1/auth/me`, {
      headers: {
        Cookie: `access_token=${accessToken}`,
      },
    });

    if (!response.ok) {
      // Token invalid - clear and redirect to login
      const loginUrl = new URL("/login", request.url);
      const res = NextResponse.redirect(loginUrl);
      res.cookies.delete("access_token");
      return res;
    }

    const user = await response.json();

    // Check user status
    if (user.status === "pending") {
      // Pending users can only access pending page
      if (!pendingAllowedRoutes.includes(pathname)) {
        return NextResponse.redirect(new URL("/pending", request.url));
      }
    } else if (user.status === "rejected") {
      // Rejected users are logged out
      const loginUrl = new URL("/login", request.url);
      const res = NextResponse.redirect(loginUrl);
      res.cookies.delete("access_token");
      return res;
    }

    // Admin route protection
    if (pathname.startsWith("/admin") && user.role !== "admin") {
      return NextResponse.redirect(new URL("/", request.url));
    }

    // Approved user on pending page - redirect to home
    if (pathname === "/pending" && user.status === "approved") {
      return NextResponse.redirect(new URL("/", request.url));
    }

    return NextResponse.next();
  } catch {
    // If backend is unreachable, allow access (let client handle it)
    return NextResponse.next();
  }
}

// Get backend URL based on environment
function getBackendUrl(request: NextRequest): string {
  // In development, use localhost
  // In production, this should be configured via environment variable
  return process.env.BACKEND_URL || "http://localhost:8000";
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\..*|api).*)",
  ],
};
