import { ReactNode, useEffect, useState } from "react";
import { redirectToLogin } from "@/api/auth";
import { isMockMode } from "@/api/mock";

type AuthStatus = "loading" | "authenticated" | "anonymous";

export default function AuthGuard({ children }: { children: ReactNode }) {
    const [status, setStatus] = useState<AuthStatus>(
        isMockMode() ? "authenticated" : "loading",
    );

    useEffect(() => {
        if (isMockMode()) return;
        let cancelled = false;
        fetch(`${import.meta.env.VITE_API_URL}/auth/check`, {
            credentials: "include",
        })
            .then((r) => (r.ok ? r.json() : null))
            .then((data) => {
                if (cancelled) return;
                setStatus(data?.user ? "authenticated" : "anonymous");
            })
            .catch(() => {
                if (!cancelled) setStatus("anonymous");
            });
        return () => {
            cancelled = true;
        };
    }, []);

    if (status === "loading") return null;
    if (status === "anonymous") {
        redirectToLogin();
        return null;
    }
    return <>{children}</>;
}
