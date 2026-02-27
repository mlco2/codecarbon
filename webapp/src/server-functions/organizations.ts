import { Organization } from "@/types/organization";
import { OrganizationReport } from "@/types/organization-report";
import { DateRange } from "react-day-picker";
import { fetchApiServer } from "@/helpers/api-server";

export async function getOrganizationEmissionsByProject(
    organizationId: string,
    dateRange: DateRange | undefined,
): Promise<OrganizationReport> {
    let endpoint = `/organizations/${organizationId}/sums`;

    if (dateRange?.from && dateRange?.to) {
        endpoint += `?start_date=${dateRange.from.toISOString()}&end_date=${dateRange.to.toISOString()}`;
    }

    const result = await fetchApiServer<OrganizationReport>(endpoint);

    // Handle case when no emissions data is found
    if (!result) {
        return {
            name: "",
            emissions: 0,
            energy_consumed: 0,
            duration: 0,
        };
    }

    return result;
}

export async function getDefaultOrgId(): Promise<string | null> {
    const orgs = await fetchApiServer<Organization[]>("/organizations");

    // Return null on failure (Pattern A - Read operation)
    if (!orgs || orgs.length === 0) {
        return null;
    }

    return orgs[0].id;
}

export async function getOrganizations(): Promise<Organization[]> {
    const orgs = await fetchApiServer<Organization[]>("/organizations");

    // Return empty array on failure (Pattern A - Read operation)
    if (!orgs) {
        return [];
    }

    return orgs;
}

export const createOrganization = async (organization: {
    name: string;
    description: string;
}): Promise<Organization> => {
    const result = await fetchApiServer<Organization>("/organizations", {
        method: "POST",
        body: JSON.stringify(organization),
    });

    // Throw on failure (Pattern B - Write operation)
    if (!result) {
        throw new Error("Failed to create organization");
    }

    return result;
};
