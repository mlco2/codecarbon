import { z } from "zod";
import { fetchApi, fetchApiJson } from "./client";

const ModelBenchmarkSchema = z.object({
    id: z.string(),
    submitted_at: z.string(),
    spec_version: z.string(),
    model_name: z.string(),
    model_revision: z.string().nullish(),
    quantization: z.string(),
    engine: z.string(),
    engine_version: z.string().nullish(),
    deployment_id: z.string().nullish(),
    deployment_label: z.string().nullish(),
    concurrency: z.number(),
    input_token_bucket: z.number().nullish(),
    gpu_model: z.string().nullish(),
    gpu_count: z.number().nullish(),
    infra_type: z.string().nullish(),
    duration: z.number(),
    it_energy_kwh: z.number(),
    input_tokens: z.number().nullish(),
    output_tokens: z.number(),
    it_energy_per_token: z.number(),
    latency_per_token_s: z.number().nullish(),
});

export type ModelBenchmark = z.infer<typeof ModelBenchmarkSchema>;

const ModelBenchmarkPageSchema = z.object({
    items: z.array(ModelBenchmarkSchema),
    total: z.number().nullish(),
});

export async function getModelBenchmarks(): Promise<{
    items: ModelBenchmark[];
    total: number;
}> {
    const page = await fetchApi(
        "/model-benchmarks?size=100",
        ModelBenchmarkPageSchema,
    );
    return { items: page.items, total: page.total ?? page.items.length };
}

export const MODEL_BENCHMARKS_EXPORT_URL = `${import.meta.env.VITE_API_URL}/model-benchmarks/export`;

// Reference snapshot in the shape EcoLogits' `measurements=` loader expects
// (a bare list of rows).
export async function getModelBenchmarksExport(): Promise<unknown[]> {
    return fetchApiJson<unknown[]>("/model-benchmarks/export");
}
