import { NextResponse } from "next/server";
import { fiefAuth } from "../../../helpers/fief";

export async function GET() {
    try {
        const currentUser = await fiefAuth.currentUser();
        return NextResponse.json(currentUser);
    } catch (error) {
        return NextResponse.json(
            { error: "Failed to fetch current user" },
            { status: 500 }
        );
    }
}
