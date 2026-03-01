import { fetchApi } from "./client";
import {
  Organization,
  OrganizationSchema,
  OrganizationReport,
  OrganizationReportSchema,
} from "./schemas";
import { DateRange } from "react-day-picker";

export async function getOrganizationEmissionsByProject(
  organizationId: string,
  dateRange: DateRange | undefined,
): Promise<OrganizationReport> {
  let endpoint = `/organizations/${organizationId}/sums`;

  if (dateRange?.from && dateRange?.to) {
    endpoint += `?start_date=${dateRange.from.toISOString()}&end_date=${dateRange.to.toISOString()}`;
  }

  try {
    return await fetchApi(endpoint, OrganizationReportSchema);
  } catch {
    return { name: "", emissions: 0, energy_consumed: 0, duration: 0 };
  }
}

export async function getOrganizations(): Promise<Organization[]> {
  try {
    return await fetchApi("/organizations", OrganizationSchema.array());
  } catch {
    return [];
  }
}

export async function createOrganization(organization: {
  name: string;
  description: string;
}): Promise<Organization> {
  return await fetchApi("/organizations", OrganizationSchema, {
    method: "POST",
    body: JSON.stringify(organization),
  });
}
