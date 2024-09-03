"use server";
import { IProjectToken } from "@/types/project";

/**
 * Retrieves the list of tokens for a given project
 */
export async function getProjectTokens(
    projectId: string
): Promise<IProjectToken[]> {
    return [
        {
            id: "85a1f3e2-73f1-44cc-bd93-1ebab8315391",
            project_id: "99bff7c9-2479-4679-bd74-a3031794c58d",
            name: "my project token",
            token: "pt_2fqJV0I3aM9gSi2OmRpHXw",
            last_used: null,
            access: 1,
        },
        {
            id: "cd26d96d-e184-423c-a00c-342bf77d1f43",
            project_id: "99bff7c9-2479-4679-bd74-a3031794c58d",
            name: "tokenName",
            token: "pt_yHslinB1hKuleB0veG73og",
            last_used: null,
            access: 2,
        },
        {
            id: "57e6fc03-4bcf-4d38-abb1-cb4f851a05e2",
            project_id: "99bff7c9-2479-4679-bd74-a3031794c58d",
            name: "tokenName",
            token: "pt_OpkkSiMkP702ereLqbXBdg",
            last_used: null,
            access: 2,
        },
        {
            id: "af9b0da2-39c7-41f1-8140-056276111cc4",
            project_id: "99bff7c9-2479-4679-bd74-a3031794c58d",
            name: "tokenName",
            token: "pt_2dQDCqi7gbg2qb4vC1Z0tA",
            last_used: null,
            access: 2,
        },
        {
            id: "2a0fd50e-7ddf-4b20-8318-84a59e7e11d7",
            project_id: "99bff7c9-2479-4679-bd74-a3031794c58d",
            name: "tokenName",
            token: "pt_0XU62PZQFHWLi3jBn4xnIw",
            last_used: null,
            access: 2,
        },
        {
            id: "722ae7b2-7cce-4ea6-918a-41761e121823",
            project_id: "99bff7c9-2479-4679-bd74-a3031794c58d",
            name: "tokenName",
            token: "pt_i__CJepb0YhOsBoSD4NyUg",
            last_used: null,
            access: 2,
        },
        {
            id: "2fcbf2f7-cda6-4309-be4a-cd0e74862a8c",
            project_id: "99bff7c9-2479-4679-bd74-a3031794c58d",
            name: "tokenName",
            token: "pt_D5ouP4pJ4UKuxGL2pnM9Mw",
            last_used: null,
            access: 2,
        },
    ];
    // try {
    //     const URL = `${process.env.NEXT_PUBLIC_API_URL}/projects/${projectId}/api-tokens`;
    //     const res = await fetch(URL);
    //     console.log("URL", URL);
    //     console.log("getProjectTokens", res);
    //     const data = await res.json();
    //     console.log("getProjectTokens", data);
    //     return data;
    // } catch (error) {
    //     // This will activate the closest `error.js` Error Boundary
    //     throw new Error("Failed to fetch data");
    // }
}

export async function createProjectToken(
    projectId: string,
    tokenName: string,
    access?: Number
): Promise<IProjectToken> {
    console.log("createProjectToken called", projectId, tokenName, access);
    try {
        const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/projects/${projectId}/api-tokens`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ name: tokenName, access }),
            }
        );
        console.log("createProjectToken", res);
        if (!res.ok) {
            // This will activate the closest `error.js` Error Boundary
            console.error("Failed to fetch data", res.statusText);
            throw new Error("Failed to fetch data");
        }
        return res.json();
    } catch (error) {
        // This will activate the closest `error.js` Error Boundary
        console.error("Failed to fetch data", error);
        throw new Error("Failed to fetch data");
    }
}
