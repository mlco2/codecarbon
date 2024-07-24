import AutoBreadcrumb from "@/components/breadcrumb";
import NavBar from "@/components/navbar";
import { getUserOrganizations } from "@/server-functions/organizations";
import Image from "next/image";
import Link from "next/link";

export default async function MainLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    const orgs = await getUserOrganizations();
    console.log("getUserOrganizations", JSON.stringify(orgs, null, 2));

    return (
        <div className="grid h-screen w-full md:grid-cols-[220px_1fr]">
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
                                width={100}
                                height={80}
                            />
                        </Link>
                    </div>
                    <NavBar orgs={orgs} />
                </div>
            </div>
            {/* Main content */}
            <div className="flex flex-col overflow-hidden">
                <div className="overflow-auto">
                    <header className="flex items-center justify-between h-14 px-4 lg:h-[60px] lg:px-6">
                        <AutoBreadcrumb />
                    </header>
                    <main className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
                        {children}
                    </main>
                </div>
            </div>
        </div>
    );
}
