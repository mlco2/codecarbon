"use client";

import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

/**
 * Home Page with 4 different behaviors possible:
 * - Displays a loading spinner if the list of organizations is being queried
 * - A 'Get Started' guide if there is no data
 * - Redirects to the first organization dashboard
 * - Redirects to the user's last visited organization dashboard if any
 */
export default function HomePage() {
  const router = useRouter();
  const [selectedOrg, setSelectedOrg] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!selectedOrg) {
      try {
        const localOrg = localStorage.getItem("organizationId");
        if (localOrg) {
          setSelectedOrg(localOrg);
        }
      } catch (error) {
        console.error("Error reading from localStorage:", error);
      }
      setLoading(false);
    }
  }, [selectedOrg]);

  if (loading) {
    return (
      <div className="flex items-center space-x-4">
        <Skeleton className="h-12 w-12 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-4 w-[250px]" />
          <Skeleton className="h-4 w-[200px]" />
        </div>
      </div>
    );
  }

  if (selectedOrg) {
    router.push(`/${selectedOrg}`);
    return null;
  }

  return (
    <div className="container mx-auto p-4">
      <Card className="max-w-md mx-auto">
        <CardHeader>
          <CardTitle>Get Started</CardTitle>
          <CardDescription>
            Create your first organization to begin
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
