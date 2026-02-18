import { getRunMetadata } from "@/server-functions/runs";
import { Emission } from "@/types/emission";
import { EmissionsTimeSeries } from "@/types/emissions-time-series";
import { ExperimentReport } from "@/types/experiment-report";
import { RunMetadata } from "@/types/run-metadata";
import { RunReport } from "@/types/run-report";

// Enhanced run report with metadata and emissions
interface EnhancedRunReport extends Omit<RunReport, "emissions"> {
    metadata?: RunMetadata;
    emissions?: Emission[];
    emissions_value: number; // Renamed from 'emissions' to avoid type conflict
}

// Extended experiment type that includes runs
interface ExperimentWithRuns extends ExperimentReport {
    runs: EnhancedRunReport[];
}

// Project type with experiments data (not extending the Project interface due to incompatible experiments field)
interface ProjectWithExperiments {
    id: string;
    name: string;
    description: string;
    public: boolean;
    organizationId: string;
    experiments: ExperimentWithRuns[];

    // Additional metadata
    date_range?: {
        startDate: string;
        endDate: string;
    };
}

interface ProjectData {
    projects: ProjectWithExperiments[];
}

/**
 * Export project data to JSON format and initiate download
 */
export function exportToJson(data: ProjectData): void {
    const jsonString = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonString], { type: "application/json" });
    // Use the first project's name for the filename
    const projectName = data.projects[0]?.name || "project";
    downloadFile(blob, `${projectName.replace(/\s+/g, "_")}_data.json`);
}

/**
 * Export experiments data to CSV format and initiate download
 * @param experiments - The experiment data to export
 * @param projectName - The name of the project for the filename
 */
export function exportExperimentsToCsv(
    experiments: ExperimentReport[],
    projectName: string,
): void {
    const csvRows: string[] = [];

    // Add header row with exact field names
    csvRows.push("experiment_id,name,emissions,energy_consumed,duration");

    if (experiments && experiments.length > 0) {
        experiments.forEach((exp) => {
            csvRows.push(
                `${exp.experiment_id},${exp.name},${exp.emissions},${exp.energy_consumed},${exp.duration}`,
            );
        });
    }

    const csvString = csvRows.join("\n");
    const blob = new Blob([csvString], { type: "text/csv;charset=utf-8;" });
    downloadFile(blob, `${projectName.replace(/\s+/g, "_")}_experiments.csv`);
}

/**
 * Export runs data to CSV format and initiate download
 * @param runs - The runs data to export
 * @param projectName - The name of the project
 * @param experimentName - Optional experiment name for the filename
 */
export async function exportRunsToCsv(
    runs: RunReport[],
    projectName: string,
    experimentName?: string,
): Promise<void> {
    // Fetch metadata for all runs concurrently
    const metadataPromises = runs.map((run) => getRunMetadata(run.runId));
    const metadataResults = await Promise.all(metadataPromises);

    // Create a map of runId to metadata for easy lookup
    const metadataMap = new Map<string, RunMetadata>();
    metadataResults.forEach((metadata, index) => {
        if (metadata) {
            metadataMap.set(runs[index].runId, metadata);
        }
    });

    const csvRows: string[] = [];

    // Extended header row with metadata fields
    csvRows.push(
        "runId,timestamp,emissions,energy_consumed,duration,os,python_version,codecarbon_version,cpu_count,cpu_model,gpu_count,gpu_model,region,provider,ram_total_size,tracking_mode",
    );

    if (runs && runs.length > 0) {
        runs.forEach((run) => {
            const metadata = metadataMap.get(run.runId);
            let row = `${run.runId},${run.timestamp},${run.emissions},${run.energy_consumed},${run.duration}`;

            // Add metadata fields if available
            if (metadata) {
                row += `,${metadata.os},${metadata.python_version},${metadata.codecarbon_version},${metadata.cpu_count},${metadata.cpu_model},${metadata.gpu_count},${metadata.gpu_model || "N/A"},${metadata.region},${metadata.provider},${metadata.ram_total_size},${metadata.tracking_mode}`;
            } else {
                // Add empty values if metadata is not available
                row += ",,,,,,,,,,,";
            }

            csvRows.push(row);
        });
    }

    const csvString = csvRows.join("\n");
    const blob = new Blob([csvString], { type: "text/csv;charset=utf-8;" });

    const fileName = experimentName
        ? `${projectName.replace(/\s+/g, "_")}_${experimentName.replace(/\s+/g, "_")}_runs.csv`
        : `${projectName.replace(/\s+/g, "_")}_runs.csv`;

    downloadFile(blob, fileName);
}

/**
 * Export emissions time series data to CSV format and initiate download
 * @param timeSeries - The emissions time series data
 * @param projectName - The name of the project
 * @param experimentName - Optional experiment name for the filename
 */
export function exportEmissionsTimeSeriesCsv(
    timeSeries: EmissionsTimeSeries,
    projectName: string,
    experimentName?: string,
): void {
    const csvRows: string[] = [];

    // Add emissions data header and rows
    csvRows.push(
        "timestamp,emissions_sum,emissions_rate,cpu_power,gpu_power,ram_power,cpu_energy,gpu_energy,ram_energy,energy_consumed",
    );

    if (timeSeries.emissions && timeSeries.emissions.length > 0) {
        timeSeries.emissions.forEach((emission) => {
            csvRows.push(
                `${emission.timestamp},${emission.emissions_sum},${emission.emissions_rate},${emission.cpu_power},${emission.gpu_power},${emission.ram_power},${emission.cpu_energy},${emission.gpu_energy},${emission.ram_energy},${emission.energy_consumed}`,
            );
        });
    }

    const csvString = csvRows.join("\n");
    const blob = new Blob([csvString], { type: "text/csv;charset=utf-8;" });

    const fileName = experimentName
        ? `${projectName.replace(/\s+/g, "_")}_${experimentName.replace(/\s+/g, "_")}_run_${timeSeries.runId}_emissions.csv`
        : `${projectName.replace(/\s+/g, "_")}_run_${timeSeries.runId}_emissions.csv`;

    downloadFile(blob, fileName);
}

/**
 * Helper function to download a file
 */
function downloadFile(blob: Blob, filename: string): void {
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);

    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    link.style.visibility = "hidden";

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
