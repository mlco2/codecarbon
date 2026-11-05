import { useEffect, useState } from "react";
import {
    getModelBenchmarks,
    getModelBenchmarksExport,
    ModelBenchmark,
    MODEL_BENCHMARKS_EXPORT_URL,
} from "@/api/modelBenchmarks";

// Experimental page: raw listing of submitted LLM energy benchmarks.

const fmt = (v: number | null | undefined, digits = 3) =>
    v === null || v === undefined ? "-" : v.toPrecision(digits);

export default function BenchmarksPage() {
    const [items, setItems] = useState<ModelBenchmark[]>([]);
    const [total, setTotal] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [copyStatus, setCopyStatus] = useState<string | null>(null);

    const copy = async (getText: () => Promise<string>, what: string) => {
        try {
            await navigator.clipboard.writeText(await getText());
            setCopyStatus(`Copied ${what}`);
        } catch (e) {
            setCopyStatus(
                `Copy failed: ${e instanceof Error ? e.message : String(e)}`,
            );
        }
    };

    useEffect(() => {
        getModelBenchmarks()
            .then((res) => {
                setItems(res.items);
                setTotal(res.total);
            })
            .catch((e) => setError(String(e?.message ?? e)))
            .finally(() => setLoading(false));
    }, []);

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-2">
                LLM energy benchmarks (experimental)
            </h1>
            {loading && <p>Loading…</p>}
            {error && <p className="text-red-500">Error: {error}</p>}
            {!loading && !error && (
                <p className="mb-4 text-muted-foreground">
                    {items.length} of {total} records
                </p>
            )}
            <div className="mb-4 flex flex-wrap items-center gap-2 text-sm">
                <button
                    className="border rounded px-2 py-1 hover:bg-muted"
                    onClick={() =>
                        copy(
                            async () =>
                                JSON.stringify(
                                    await getModelBenchmarksExport(),
                                    null,
                                    2,
                                ),
                            "EcoLogits reference JSON",
                        )
                    }
                >
                    Copy EcoLogits reference JSON
                </button>
                <button
                    className="border rounded px-2 py-1 hover:bg-muted"
                    onClick={() =>
                        copy(
                            async () => MODEL_BENCHMARKS_EXPORT_URL,
                            "export URL",
                        )
                    }
                >
                    Copy export URL
                </button>
                {copyStatus && (
                    <span className="text-muted-foreground">{copyStatus}</span>
                )}
            </div>
            <p className="mb-4 text-xs text-muted-foreground">
                Save the JSON to a file, then{" "}
                <code>
                    EcoLogits.init(providers=[&quot;local&quot;],
                    measurements=&quot;path/to/file.json&quot;)
                </code>{" "}
                (or pass the export URL as <code>measurements</code>).
            </p>
            <div className="overflow-x-auto">
                <table className="text-sm border-collapse">
                    <thead>
                        <tr className="text-left border-b">
                            {[
                                "Submitted",
                                "Model",
                                "Quant",
                                "Engine",
                                "Deployment",
                                "GPU",
                                "Conc.",
                                "In bucket",
                                "Duration (s)",
                                "Energy (kWh)",
                                "In tokens",
                                "Out tokens",
                                "kWh / token",
                                "Latency / token (s)",
                                "Spec",
                            ].map((h) => (
                                <th
                                    key={h}
                                    className="px-2 py-1 whitespace-nowrap"
                                >
                                    {h}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {items.map((b) => (
                            <tr key={b.id} className="border-b align-top">
                                <td className="px-2 py-1 whitespace-nowrap">
                                    {new Date(b.submitted_at).toLocaleString()}
                                </td>
                                <td className="px-2 py-1">
                                    {b.model_name}
                                    {b.model_revision && (
                                        <span className="text-muted-foreground">
                                            {" "}
                                            @{b.model_revision.slice(0, 8)}
                                        </span>
                                    )}
                                </td>
                                <td className="px-2 py-1">{b.quantization}</td>
                                <td className="px-2 py-1 whitespace-nowrap">
                                    {b.engine} {b.engine_version ?? ""}
                                </td>
                                <td className="px-2 py-1">
                                    {b.deployment_label ??
                                        b.deployment_id ??
                                        "-"}
                                </td>
                                <td className="px-2 py-1 whitespace-nowrap">
                                    {b.gpu_count ? `${b.gpu_count}× ` : ""}
                                    {b.gpu_model ?? "-"}
                                    {b.infra_type ? ` (${b.infra_type})` : ""}
                                </td>
                                <td className="px-2 py-1 text-right">
                                    {b.concurrency}
                                </td>
                                <td className="px-2 py-1 text-right">
                                    {b.input_token_bucket ?? "-"}
                                </td>
                                <td className="px-2 py-1 text-right">
                                    {b.duration.toFixed(1)}
                                </td>
                                <td className="px-2 py-1 text-right">
                                    {fmt(b.it_energy_kwh)}
                                </td>
                                <td className="px-2 py-1 text-right">
                                    {b.input_tokens ?? "-"}
                                </td>
                                <td className="px-2 py-1 text-right">
                                    {b.output_tokens}
                                </td>
                                <td className="px-2 py-1 text-right">
                                    {fmt(b.it_energy_per_token)}
                                </td>
                                <td className="px-2 py-1 text-right">
                                    {fmt(b.latency_per_token_s)}
                                </td>
                                <td className="px-2 py-1">{b.spec_version}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
