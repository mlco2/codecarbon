"use client";

import { useState } from "react";
import { createExperiment } from "@/server-functions/experiments";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Experiment } from "@/types/experiment";
import GeneralModal from "./ui/modal";
import { Separator } from "./ui/separator";

export default function CreateExperimentModal({
    projectId,
    isOpen,
    onClose,
    onExperimentCreated,
}: {
    projectId: string;
    isOpen: boolean;
    onClose: () => void;
    onExperimentCreated: () => void;
}) {
    const initialData: Experiment = {
        name: "",
        description: "",
        on_cloud: false,
        project_id: projectId,
    };
    const initialSavedData: Experiment = {
        project_id: projectId,
        name: "",
        description: "",
        on_cloud: false,
    };
    const handleSave = async (data: Experiment) => {
        const newExperiment: Experiment = await createExperiment(data);
        await onExperimentCreated(); // Call the callback to refresh the project list
        return newExperiment;
    };

    const renderForm = (data: Experiment, setData: any) => (
        <div>
            <h2 className="text-xl font-bold mb-4">Create new experiment</h2>
            <Separator className="mb-4" />
            <Input
                type="text"
                value={data.name}
                onChange={(e) => setData({ ...data, name: e.target.value })}
                placeholder="Experiment Name"
                className={"mt-4 mb-4"}
            />
            <Input
                type="text"
                value={data.description}
                onChange={(e) =>
                    setData({ ...data, description: e.target.value })
                }
                placeholder="Experiment Description"
                className={"mt-4 mb-4"}
            />
            <Input
                type="text"
                value={data.country_name}
                onChange={(e) =>
                    setData({ ...data, country_name: e.target.value })
                }
                placeholder="Country Name"
                className={"mt-4 mb-4"}
            />
            <Input
                type="text"
                value={data.country_iso_code}
                onChange={(e) =>
                    setData({ ...data, country_iso_code: e.target.value })
                }
                placeholder="Country ISO Code"
                className={"mt-4 mb-4"}
            />
            <Input
                type="text"
                value={data.region}
                onChange={(e) => setData({ ...data, region: e.target.value })}
                placeholder="Region"
                className={"mt-4 mb-4"}
            />
            {/** On_cloud boolean checkbox */}
            <div className="flex items-center mb-4">
                <label htmlFor="on_cloud" className="mr-2">
                    On Cloud
                </label>
                <Input
                    type="checkbox"
                    id="on_cloud"
                    checked={data.on_cloud}
                    onChange={(e) =>
                        setData({ ...data, on_cloud: e.target.checked })
                    }
                />
            </div>
            {data.on_cloud && (
                <div>
                    <Input
                        type="text"
                        value={data.cloud_provider}
                        onChange={(e) =>
                            setData({ ...data, cloud_provider: e.target.value })
                        }
                        placeholder="Cloud Provider"
                        className={"mt-4 mb-4"}
                    />
                    <Input
                        type="text"
                        value={data.cloud_region}
                        onChange={(e) =>
                            setData({ ...data, cloud_region: e.target.value })
                        }
                        placeholder="Cloud Region"
                        className={"mt-4 mb-4"}
                    />
                </div>
            )}
        </div>
    );
    const renderSavedData = (data: Experiment, setSavedData: any) => (
        <div>
            <h2 className="text-xl font-bold mb-4">
                Experiment {data.name} Created
            </h2>
        </div>
    );

    return (
        <GeneralModal
            isOpen={isOpen}
            onClose={onClose}
            onSave={handleSave}
            initialData={initialData}
            initialSavedData={initialSavedData}
            renderForm={renderForm}
            renderSavedData={renderSavedData}
        />
    );
}
