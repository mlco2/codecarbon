import React from "react";
import { Loader2 } from "lucide-react";

export default function Loader() {
    return (
        <div className="flex min-h-screen justify-center items-center flex-col">
            <Loader2 className="h-16 w-16 animate-spin text-primary" />
        </div>
    );
}
