import { IProjectToken } from "@/types/project";
import { fetchApi } from "@/utils/api";

/**
 * Retrieves the list of tokens for a given project
 */
export async function getProjectTokens(
    projectId: string,
): Promise<IProjectToken[]> {
    const data = await fetchApi<IProjectToken[]>(
        `/projects/${projectId}/api-tokens`,
    );

    if (!data) {
        throw new Error("Failed to fetch project tokens");
    }

    return data;
}

export async function createProjectToken(
    projectId: string,
    tokenName: string,
    access?: Number,
): Promise<IProjectToken> {
    const result = await fetchApi<IProjectToken>(
        `/projects/${projectId}/api-tokens`,
        {
            method: "POST",
            body: JSON.stringify({ name: tokenName, access }),
        },
    );

    if (!result) {
        throw new Error("Failed to create project token");
    }

    return result;
}
export async function deleteProjectToken(
    projectId: string,
    tokenId: string,
): Promise<void> {
    await fetchApi(`/projects/${projectId}/api-tokens/${tokenId}`, {
        method: "DELETE",
    });
}
