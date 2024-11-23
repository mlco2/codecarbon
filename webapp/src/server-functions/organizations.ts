import { Organization } from "@/types/organization";
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
export async function getOrganizations(): Promise<Organization[] | undefined> {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/organizations`);

    if (!res.ok) {
        console.warn("error fetching organizations list");
        return;
    }
    try {
        const orgs = await res.json();
    } catch (err) {
        console.warn("error processing organizations list");
    }
    return;
}

export const createOrganization = async (organization: {
    name: string;
    description: string;
}): Promise<Organization> => {
    const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/organizations`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(organization),
        },
    );
    const data = await response.json();
    return data;
};
