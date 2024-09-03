export interface Project {
    id: string;
    name: string;
    description: string;
    organizationId: string;
}

export interface IProjectToken {
    id: string;
    project_id: string;
    last_used: string | null;
    name: string;
    token: string;
    access: number;
}
