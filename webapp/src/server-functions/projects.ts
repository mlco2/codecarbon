import { Project, ProjectInputs } from "@/types/project";
import { fetchApiServer } from "@/helpers/api-server";

export const createProject = async (
    organizationId: string,
    project: { name: string; description: string },
): Promise<Project> => {
    const result = await fetchApiServer<Project>("/projects", {
        method: "POST",
        body: JSON.stringify({
            ...project,
            organization_id: organizationId,
        }),
    });

    // Throw on failure (Pattern B - Write operation)
    if (!result) {
        throw new Error("Failed to create project");
    }

    return result;
};

export const updateProject = async (
    projectId: string,
    project: ProjectInputs,
): Promise<Project> => {
    const result = await fetchApiServer<Project>(`/projects/${projectId}`, {
        method: "PATCH",
        body: JSON.stringify(project),
    });

    // Throw on failure (Pattern B - Write operation)
    if (!result) {
        throw new Error("Failed to update project");
    }

    return result;
};

export const getProjects = async (
    organizationId: string,
): Promise<Project[] | null> => {
    const projects = await fetchApiServer<Project[]>(
        `/projects?organization=${organizationId}`,
    );
    if (!projects) {
        return [];
    }
    return projects;
};

export const getOneProject = async (
    projectId: string,
): Promise<Project | null> => {
    const project = await fetchApiServer<Project>(`/projects/${projectId}`);
    return project;
};

export const deleteProject = async (projectId: string): Promise<void> => {
    await fetchApiServer(`/projects/${projectId}`, {
        method: "DELETE",
    });
};
