"use client";

import NavBar from "@/components/navbar";
import dynamic from "next/dynamic";
import Image from "next/image";
import Link from "next/link";
import { Organization } from "@/types/organization";
import { fetcher } from "@/helpers/swr";
import { useEffect, useState } from "react";
import useSWR from "swr";
import Loader from "@/components/loader";

const MobileHeader = dynamic(() => import("@/components/mobile-header"), {
    ssr: false,
});

export default function MainLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    const [initialLoad, setInitialLoad] = useState(true);
    
    // Fetch organizations for the navbar
    const { data: orgs, error } = useSWR<Organization[]>('/organizations', fetcher, {
        revalidateOnFocus: false, 
    });
    
    useEffect(() => {
        // Set initial load to false after first data fetch
        if (orgs || error) {
            // Wait a small delay to ensure smooth transition
            const timer = setTimeout(() => {
                setInitialLoad(false);
            }, 100);
            
            return () => clearTimeout(timer);
        }
    }, [orgs, error]);
    
    return (
        <div className="grid h-screen w-full md:grid-cols-[220px_1fr]">
            {/* Side bar that shows only on screens larger than 768px */}
            <div className="hidden border-r bg-muted/40 md:block">
                <div className="flex h-full max-h-screen flex-col gap-2">
                    <div className="flex h-14 items-center px-4 lg:h-[80px] lg:px-6">
                        <Link
                            href="/home"
                            className="flex flex-1 justify-center items-center gap-2 pt-6 font-semibold"
                        >
                            <Image
                                src="/logo.svg"
                                alt="Logo"
                                width={95}
                                height={89}
                                priority
                            />
                        </Link>
                    </div>
                    <NavBar orgs={orgs || []} />
                </div>
            </div>

            {/* Main content */}
            <div className="flex flex-col overflow-hidden">
                <div className="overflow-auto">
                    <MobileHeader orgs={orgs || []} />
                    <main className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
                        {initialLoad ? (
                            <div className="flex h-full items-center justify-center">
                                <Loader />
                            </div>
                        ) : (
                            children
                        )}
                    </main>
                </div>
            </div>
        </div>
    );
}
