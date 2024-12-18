import { Emission } from "@/types/emission";
import { RunMetadata } from "@/types/run-metadata";

export interface EmissionsTimeSeries {
    runId: string;
    emissions: Emission[];
    metadata: RunMetadata;
}
