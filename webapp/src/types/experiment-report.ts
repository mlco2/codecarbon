export interface ExperimentReport {
    experiment_id: string;
    name: string;
    emissions: number;
    energy_consumed: number;
    water_consumed: number;
    duration: number;
    description?: string;
}
