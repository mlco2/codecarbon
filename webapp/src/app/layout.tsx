"use client";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { FiefAuthProvider } from "@fief/fief/nextjs/react";
import { ThemeProvider } from "@/components/ui/theme-provider";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className={inter.className}>
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
            </body>
        </html>
    );
}
