import { SWRConfig } from "swr";

export const SWRProvider = ({ children }: { children: React.ReactNode }) => {
    return <SWRConfig>{children}</SWRConfig>;
};

export const fetcher = async (url: string) => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${url}`);
    if (!res.ok) {
        console.error("Failed to fetch data", res.statusText);
        throw new Error("Failed to fetch data");
    }
    return res.json();
};
