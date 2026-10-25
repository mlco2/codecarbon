import useSWR from "swr";

import { Organization } from "@/api/schemas";
import { fetcher } from "@/api/swr";

/**
 * The organization's name for breadcrumbs. While it is fetched, falls back to
 * the name the navigation cached, but only when that cache is for this same
 * organization, then to the bare id.
 */
export function useOrganizationName(organizationId: string | undefined) {
    const { data: organization } = useSWR<Organization>(
        organizationId ? `/organizations/${organizationId}` : null,
        fetcher,
        { revalidateOnFocus: false },
    );

    let cachedName: string | null = null;
    try {
        if (localStorage.getItem("organizationId") === organizationId) {
            cachedName = localStorage.getItem("organizationName");
        }
    } catch {
        cachedName = null;
    }

    return organization?.name || cachedName || organizationId || "";
}
