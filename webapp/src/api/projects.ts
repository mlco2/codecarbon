import { fetchApi, fetchApiVoid } from "./client";
import {
  Project,
  ProjectSchema,
  ProjectInputs,
} from "./schemas";

export async function createProject(
  organizationId: string,
  project: { name: string; description: string },
): Promise<Project> {
  return await fetchApi("/projects", ProjectSchema, {
    method: "POST",
    body: JSON.stringify({
      ...project,
      organization_id: organizationId,
    }),
  });
}

export async function updateProject(
  projectId: string,
  project: ProjectInputs,
): Promise<Project> {
  return await fetchApi(`/projects/${projectId}`, ProjectSchema, {
    method: "PATCH",
    body: JSON.stringify(project),
  });
}

export async function getProjects(
  organizationId: string,
): Promise<Project[]> {
  try {
    return await fetchApi(
      `/projects?organization=${organizationId}`,
      ProjectSchema.array(),
    );
  } catch {
    return [];
  }
}

export async function getOneProject(
  projectId: string,
): Promise<Project | null> {
  try {
    return await fetchApi(`/projects/${projectId}`, ProjectSchema);
  } catch {
    return null;
  }
}

export async function deleteProject(projectId: string): Promise<void> {
  await fetchApiVoid(`/projects/${projectId}`, {
    method: "DELETE",
  });
}
