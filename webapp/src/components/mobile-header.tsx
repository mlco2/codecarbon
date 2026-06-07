import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Organization } from "@/api/schemas";
import { Menu } from "lucide-react";
import { Link } from "react-router-dom";
import { useState } from "react";
import NavBar from "./navbar";

export default function MobileHeader({
    orgs,
}: {
    orgs: Organization[] | undefined;
}) {
    const [isSheetOpen, setSheetOpened] = useState(false);

    return (
        <header className="flex items-center justify-between h-14 lg:hidden lg:h-0 px-4">
            {/* Drawer that shows only on small screens */}
            <Sheet open={isSheetOpen} onOpenChange={setSheetOpened}>
                <SheetTrigger asChild onClick={() => setSheetOpened(true)}>
                    <Button
                        variant="outline"
                        size="icon"
                        className="shrink-0 md:hidden"
                    >
                        <Menu className="h-5 w-5" />
                        <span className="sr-only">Toggle navigation menu</span>
                    </Button>
                </SheetTrigger>
                <SheetContent
                    side="left"
                    className="flex flex-col w-[220px] p-0"
                >
                    <div className="flex h-14 items-center px-4 lg:h-[80px] lg:px-6">
                        <Link
                            to="/home"
                            onClick={() => setSheetOpened(false)}
                            className="flex flex-1 justify-center items-center gap-2 pt-6 font-semibold"
                        >
                            <img
                                src="/logo.svg"
                                alt="Logo"
                                width={95}
                                height={89}
                            />
                        </Link>
                    </div>
                    <NavBar orgs={orgs} setSheetOpened={setSheetOpened} />
                </SheetContent>
            </Sheet>
        </header>
    );
}
