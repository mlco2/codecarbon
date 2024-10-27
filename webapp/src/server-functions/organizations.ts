import { OrganizationReport } from "@/types/organization-report";
import { DateRange } from "react-day-picker";

export async function getOrganizationEmissionsByProject(
    organizationId: string,
    dateRange: DateRange | undefined,
): Promise<OrganizationReport | null> {
    let url = `${process.env.NEXT_PUBLIC_API_URL}/organizations/${organizationId}/sums`;

    if (dateRange) {
        url += `?start_date=${dateRange.from?.toISOString()}&end_date=${dateRange.to?.toISOString()}`;
    }

    const res = await fetch(url);
    const result = await res.json();
    if (!res.ok) {
        // throw new Error("Failed to fetch /organizations");
        console.warn("error fetching organizations list");
        return null;
    }
    return {
        name: result.name,
        emissions: result.emissions * 1000,
        energy_consumed: result.energy_consumed * 1000,
        duration: result.duration,
    };
}

export async function getDefaultOrgId(): Promise<string | null> {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/organizations`);

    if (!res.ok) {
        // throw new Error("Failed to fetch /organizations");
        console.warn("error fetching organizations list");
        return null;
    }
    try {
        const orgs = await res.json();
        if (orgs.length > 0) {
            return orgs[0].id;
        }
    } catch (err) {
        console.warn("error processing organizations list");
    }
    return null;
}
