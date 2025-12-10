"use client";

import { FiefAuthProvider } from "@fief/fief/nextjs/react";
import { SessionProvider } from "next-auth/react";
import { IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { SWRProvider } from "../helpers/swr";
import { ThemeProvider } from "next-themes";
import { Toaster } from "@/components/ui/sonner";
import ClientProvider from "@/components/client-provider";

const font = IBM_Plex_Mono({ weight: "400", subsets: ["latin"] });

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en" suppressHydrationWarning>
            {/* suppressHydrationWarning is a Next theme recommendation */}
            <body className={font.className}>
                {/* <SessionProvider> */}
                    <SWRProvider>
                        {/* <FiefAuthProvider
                            currentUserPath={`${process.env.NEXT_PUBLIC_API_URL}/auth/check`}
                            state={{
                                userinfo: null,
                                accessTokenInfo: null,
                            }}
                        > */}
                            <ThemeProvider
                                attribute="class"
                                defaultTheme="dark"
                                forcedTheme="dark"
                                disableTransitionOnChange
                            >
                                {/* {children}
                                 */}
                                         <ClientProvider>{children}</ClientProvider>

                                <Toaster />
                            </ThemeProvider>
                        {/* </FiefAuthProvider> */}
                    </SWRProvider>
                {/* </SessionProvider> */}
            </body>
        </html>
    );
}
