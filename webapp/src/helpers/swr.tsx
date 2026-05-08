import { SWRConfig } from "swr";

export const SWRProvider = ({ children }: { children: React.ReactNode }) => {
    return <SWRConfig>{children}</SWRConfig>;
};

export const fetcher = async (url: string) => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${url}`, {
        credentials: "include",
    });

    if (!res.ok) {
        if (res.status === 401) {
            window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/auth/login?redirect=${process.env.NEXT_PUBLIC_BASE_URL}/home?auth=true`;
            return null;
        }
        console.error("Failed to fetch data", res.statusText);
        throw new Error("Failed to fetch data");
    }

    return res.json();
};
