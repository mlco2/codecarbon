import { fetchApi, fetchApiVoid } from "./client";
import { IProjectToken, ProjectTokenSchema } from "./schemas";

export async function getProjectTokens(
  projectId: string,
): Promise<IProjectToken[]> {
  try {
    return await fetchApi(
      `/projects/${projectId}/api-tokens`,
      ProjectTokenSchema.array(),
    );
  } catch {
    return [];
  }
}

export async function createProjectToken(
  projectId: string,
  tokenName: string,
  access?: number,
): Promise<IProjectToken> {
  return await fetchApi(
    `/projects/${projectId}/api-tokens`,
    ProjectTokenSchema,
    {
      method: "POST",
      body: JSON.stringify({ name: tokenName, access }),
    },
  );
}

export async function deleteProjectToken(
  projectId: string,
  tokenId: string,
): Promise<void> {
  await fetchApiVoid(`/projects/${projectId}/api-tokens/${tokenId}`, {
    method: "DELETE",
  });
}
