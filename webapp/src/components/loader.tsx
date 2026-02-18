import React from "react";
import { Loader2 } from "lucide-react";

export default function Loader() {
    return (
        <div className="flex justify-center items-center flex-col h-[calc(100vh-2rem)] lg:h-[calc(100vh-3rem)]">
            <Loader2 className="h-16 w-16 animate-spin text-primary" />
        </div>
    );
}
