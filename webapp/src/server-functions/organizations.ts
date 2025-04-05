import { Organization } from "@/types/organization";
import { OrganizationReport } from "@/types/organization-report";
import { DateRange } from "react-day-picker";
import { fetchApiServer } from "@/helpers/api-server";

export async function getOrganizationEmissionsByProject(
    organizationId: string,
    dateRange: DateRange | undefined,
): Promise<OrganizationReport | null> {
    try {
        let endpoint = `/organizations/${organizationId}/sums`;

        if (dateRange?.from && dateRange?.to) {
            endpoint += `?start_date=${dateRange.from.toISOString()}&end_date=${dateRange.to.toISOString()}`;
        }

        const result = await fetchApiServer<any>(endpoint);

        if (!result) {
            return null;
        }

        // Handle case when no emissions data is found
        if (!result || result === null) {
            // Return zeros for all metrics
            return {
                name: "",
                emissions: 0,
                energy_consumed: 0,
                duration: 0,
            };
        }

        return {
            name: result.name || "",
            emissions: result.emissions || 0,
            energy_consumed: result.energy_consumed || 0,
            duration: result.duration || 0,
        };
    } catch (error) {
        console.error("Error fetching organization emissions:", error);
        // Return default values if there's an error
        return {
            name: "",
            emissions: 0,
            energy_consumed: 0,
            duration: 0,
        };
    }
}

export async function getDefaultOrgId(): Promise<string | null> {
    try {
        const orgs = await fetchApiServer<Organization[]>("/organizations");
        if (!orgs) {
            return null;
        }

        if (orgs.length > 0) {
            return orgs[0].id;
        }
    } catch (err) {
        console.warn("error processing organizations list", err);
    }
    return null;
}

export async function getOrganizations(): Promise<Organization[]> {
    try {
        const orgs = await fetchApiServer<Organization[]>("/organizations");
        if (!orgs) {
            return [];
        }

        return orgs;
    } catch (err) {
        console.warn("error fetching organizations list", err);
        return [];
    }
}

export const createOrganization = async (organization: {
    name: string;
    description: string;
}): Promise<Organization | null> => {
    return fetchApiServer<Organization>("/organizations", {
        method: "POST",
        body: JSON.stringify(organization),
    });
};
