"use client";

import { useState, useEffect } from "react";
import { Project } from "@/types/project";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ProjectTokensTable } from "./projectTokens/projectTokenTable";
import { updateProject } from "@/server-functions/projects";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";

interface ProjectSettingsModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    project: Project;
    onProjectUpdated: () => void;
}

export default function ProjectSettingsModal({
    open,
    onOpenChange,
    project,
    onProjectUpdated,
}: ProjectSettingsModalProps) {
    const router = useRouter();
    const [name, setName] = useState(project.name || "");
    const [description, setDescription] = useState(project.description || "");
    const [isPublic, setIsPublic] = useState(project.public || false);
    const [isSaving, setIsSaving] = useState(false);
    const [activeTab, setActiveTab] = useState("general");

    // Update form when project changes
    useEffect(() => {
        setName(project.name || "");
        setDescription(project.description || "");
        setIsPublic(project.public || false);
    }, [project]);

    const handleSave = async () => {
        setIsSaving(true);
        try {
            await updateProject(project.id, {
                name,
                description,
                public: isPublic,
            });
            toast.success("Project settings updated successfully");
            onProjectUpdated();
        } catch (error) {
            console.error("Error updating project:", error);
            toast.error("Failed to update project settings");
        } finally {
            setIsSaving(false);
            onOpenChange(false);
            router.refresh();
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px] md:max-w-[700px] max-h-[90vh] overflow-y-auto p-8">
                <DialogHeader>
                    <DialogTitle>Project Settings</DialogTitle>
                    <DialogDescription>
                        Manage your project settings and API tokens
                    </DialogDescription>
                </DialogHeader>

                <Tabs
                    value={activeTab}
                    onValueChange={setActiveTab}
                    className="w-full"
                >
                    <TabsList className="w-full">
                        <TabsTrigger value="general" className="flex-1">
                            General
                        </TabsTrigger>
                        <TabsTrigger value="tokens" className="flex-1">
                            API Tokens
                        </TabsTrigger>
                    </TabsList>

                    <TabsContent value="general" className="mt-4 space-y-4">
                        <div className="space-y-4">
                            <div>
                                <Label htmlFor="name">Project Name</Label>
                                <Input
                                    id="name"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder="Enter project name"
                                    className="mt-1"
                                />
                            </div>
                            <div>
                                <Label htmlFor="description">
                                    Project Description
                                </Label>
                                <Input
                                    id="description"
                                    value={description}
                                    onChange={(e) =>
                                        setDescription(e.target.value)
                                    }
                                    placeholder="Enter project description"
                                    className="mt-1"
                                />
                            </div>
                            <div className="flex items-center space-x-2">
                                <Switch
                                    id="isPublic"
                                    checked={isPublic}
                                    onCheckedChange={setIsPublic}
                                />
                                <Label htmlFor="isPublic">
                                    Make project public
                                </Label>
                                <p className="text-sm text-muted-foreground ml-2">
                                    (enables public sharing link)
                                </p>
                            </div>
                        </div>

                        <DialogFooter className="mt-6">
                            <Button onClick={handleSave} disabled={isSaving}>
                                {isSaving ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Saving...
                                    </>
                                ) : (
                                    "Save Changes"
                                )}
                            </Button>
                        </DialogFooter>
                    </TabsContent>

                    <TabsContent value="tokens" className="mt-4">
                        <ProjectTokensTable projectId={project.id} />
                    </TabsContent>
                </Tabs>
            </DialogContent>
        </Dialog>
    );
}
