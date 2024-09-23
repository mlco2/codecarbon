export interface RunMetadata {
    timestamp: string;
    experiment_id: string;
    os: string;
    python_version: string;
    codecarbon_version: string;
    cpu_count: number;
    cpu_model: string;
    gpu_count: number;
    gpu_model: string;
    longitude: number;
    latitude: number;
    region: string;
    provider: string;
    ram_total_size: number;
    tracking_mode: string;
}
