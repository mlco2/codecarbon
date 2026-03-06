import NavBar from "@/components/navbar";
import { lazy, Suspense, useEffect, useState } from "react";
import { Link, Outlet } from "react-router-dom";
import { Organization } from "@/api/schemas";
import { fetcher } from "@/api/swr";
import useSWR from "swr";
import Loader from "@/components/loader";

const MobileHeader = lazy(() => import("@/components/mobile-header"));

export default function DashboardLayout() {
  const [initialLoad, setInitialLoad] = useState(true);

  const { data: orgs, error } = useSWR<Organization[]>(
    "/organizations",
    fetcher,
    { revalidateOnFocus: false },
  );

  useEffect(() => {
    if (orgs || error) {
      const timer = setTimeout(() => {
        setInitialLoad(false);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [orgs, error]);

  return (
    <div className="grid h-screen w-full md:grid-cols-[220px_1fr]">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-4 focus:bg-background focus:text-foreground"
      >
        Skip to main content
      </a>
      <nav aria-label="Sidebar" className="hidden border-r bg-muted/40 md:block">
        <div className="flex h-full max-h-screen flex-col gap-2">
          <div className="flex h-14 items-center px-4 lg:h-[80px] lg:px-6">
            <Link
              to="/home"
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
          <NavBar orgs={orgs || []} />
        </div>
      </nav>

      <div className="flex flex-col overflow-hidden">
        <div className="overflow-auto">
          <Suspense fallback={null}>
            <MobileHeader orgs={orgs || []} />
          </Suspense>
          <main id="main-content" className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            {initialLoad ? (
              <div className="flex h-full items-center justify-center">
                <Loader />
              </div>
            ) : (
              <Outlet />
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
