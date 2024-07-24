import { Organization } from "@/types/organization";

/**
 * Retrieves the list of organizations for a given user
 * @TODO Use the user id to fetch the organizations the user is part of
 */
export async function getUserOrganizations(): Promise<Organization[]> {
    const res = await fetch(`${process.env.API_URL}/organizations`, {
        next: { revalidate: 60 }, // Revalidate every minute
    });

    if (!res.ok) {
        // This will activate the closest `error.js` Error Boundary
        throw new Error("Failed to fetch data");
    }

    return res.json();
}
