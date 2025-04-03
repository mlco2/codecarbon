export interface Experiment {
    timestamp: string;
    name: string;
    description: string;
    on_cloud: boolean;
    project_id: string;
    country_name?: string;
    country_iso_code?: string;
    region?: string;
    cloud_provider?: string;
    cloud_region?: string;
}
