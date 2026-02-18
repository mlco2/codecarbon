export interface Project {
    id: string;
    name: string;
    description: string;
    public: boolean;
    organizationId: string;
    experiments: string[];
}

export interface ProjectInputs {
    name: string;
    description: string;
    public: boolean;
}

export interface IProjectToken {
    id: string;
    project_id: string;
    last_used: string | null;
    name: string;
    token: string;
    access: number;
}
