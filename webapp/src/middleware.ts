import type { NextRequest } from "next/server";

import { fiefAuth } from "./helpers/fief";

const authMiddleware = fiefAuth.middleware([
    {
        matcher:
            "/((?!api|_next/static|_next/image|favicon.ico|icons/|public/).*)",
        parameters: {},
    },
]);

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

    return authMiddleware(request);
}
