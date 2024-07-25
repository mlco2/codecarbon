import { Organization } from "@/types/organization";

/**
 * Retrieves the list of organizations for a given user
 * @TODO Use the user id to fetch the organizations the user is part of
 */
export async function getUserOrganizations(): Promise<Organization[]> {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/organizations`);

    if (!res.ok) {
        // This will activate the closest `error.js` Error Boundary
        console.error("Failed to fetch data", res.statusText);
        throw new Error("Failed to fetch data");
    }
    return res.json();
}
