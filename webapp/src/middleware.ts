import type { NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
    const pathname = request.nextUrl.pathname;

    // Skip auth for public routes
    if (
        pathname === "/" ||
        pathname.startsWith("/public/") ||
        pathname.startsWith("/api/public/")
    ) {
        return;
    }
}
