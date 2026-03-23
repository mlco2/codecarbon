import { ReactNode } from "react";

function hasSessionCookie(): boolean {
  return document.cookie.split(";").some((c) => c.trim().startsWith("user_session="));
}

export default function AuthGuard({ children }: { children: ReactNode }) {
  if (!hasSessionCookie()) {
    window.location.href = `${import.meta.env.VITE_API_URL}/auth/login?redirect=${import.meta.env.VITE_BASE_URL}/home?auth=true`;
    return null;
  }
  return <>{children}</>;
}
