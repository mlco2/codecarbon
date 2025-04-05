import { Project, ProjectInputs } from "@/types/project";
import { fetchApiServer } from "@/helpers/api-server";

export const createProject = async (
    organizationId: string,
    project: { name: string; description: string },
): Promise<Project | null> => {
    const result = await fetchApiServer<Project>("/projects", {
        method: "POST",
        body: JSON.stringify({
            ...project,
            organization_id: organizationId,
        }),
    });

    if (!result) {
        return null;
    }
    return result;
};

export const updateProject = async (
    projectId: string,
    project: ProjectInputs,
): Promise<Project | null> => {
    const result = await fetchApiServer<Project>(`/projects/${projectId}`, {
        method: "PATCH",
        body: JSON.stringify(project),
    });
    if (!result) {
        return null;
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
    console.log("project", JSON.stringify(project, null, 2));
    if (!project) {
        return null;
    }
    return project;
};
