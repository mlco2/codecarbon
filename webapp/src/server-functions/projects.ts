import { Project, ProjectInputs } from "@/types/project";
import { fetchApiServer } from "@/helpers/api-server";

export const createProject = async (
    organizationId: string,
    project: { name: string; description: string },
): Promise<Project> => {
    return fetchApiServer<Project>("/projects", {
        method: "POST",
        body: JSON.stringify({
            ...project,
            organization_id: organizationId,
        }),
    });
};

export const updateProject = async (
    projectId: string,
    project: ProjectInputs,
): Promise<Project> => {
    return fetchApiServer<Project>(`/projects/${projectId}`, {
        method: "PATCH",
        body: JSON.stringify(project),
    });
};

export const getProjects = async (
    organizationId: string,
): Promise<Project[]> => {
    return fetchApiServer<Project[]>(
        `/projects?organization=${organizationId}`,
    );
};

export const getOneProject = async (projectId: string): Promise<Project> => {
    return fetchApiServer<Project>(`/projects/${projectId}`);
};
