import { Project } from "@/types/project";

export const createProject = async (
    organizationId: string,
    project: { name: string; description: string },
): Promise<Project> => {
    const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/projects`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                ...project,
                organization_id: organizationId,
            }),
        },
    );
    const data = await response.json();
    return data;
};

export const getProjects = async (
    organizationId: string,
): Promise<Project[]> => {
    const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/projects?organization=${organizationId}`,
    );
    const data = await response.json();
    return data;
};
