export interface Emission {
    emission_id: string;
    timestamp: string;
    emissions_sum: number;
    emissions_rate: number;
    cpu_power: number;
    gpu_power: number;
    ram_power: number;
    cpu_energy: number;
    gpu_energy: number;
    ram_energy: number;
    energy_consumed: number;
}
