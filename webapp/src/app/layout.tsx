"use client";

import { ThemeProvider } from "@/components/ui/theme-provider";
import { FiefAuthProvider } from "@fief/fief/nextjs/react";
import { Inter } from "next/font/google";
import "./globals.css";
import { SWRProvider } from "../helpers/swr";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <SWRProvider>
                    <FiefAuthProvider
                        currentUserPath="/api/current-user"
                        state={{
                            userinfo: null,
                            accessTokenInfo: null,
                        }}
                    >
                        <ThemeProvider
                            attribute="class"
                            defaultTheme="dark"
                            enableSystem
                            disableTransitionOnChange
                        >
                            {children}
                        </ThemeProvider>
                    </FiefAuthProvider>
                </SWRProvider>
            </body>
        </html>
    );
}
