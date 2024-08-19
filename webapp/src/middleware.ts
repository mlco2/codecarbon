import type { NextRequest } from "next/server";

import { fiefAuth } from "./helpers/fief";

const authMiddleware = fiefAuth.middleware([
    {
        matcher: "/((?!api|_next/static|_next/image|favicon.ico).*)",
        parameters: {},
    },
]);

export async function middleware(request: NextRequest) {
    const pathname = request.nextUrl.pathname;
    console.log(pathname)
    console.log(request.nextUrl)
    if (pathname === "/") {
        return;
    }
    console.log("Not on /")
    return authMiddleware(request);
}
