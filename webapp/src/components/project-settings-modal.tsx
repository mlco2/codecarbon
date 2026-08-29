import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { updateProject } from "@/api/projects";
import { Project } from "@/api/schemas";
import { ProjectTokensTable } from "./projectTokens/projectTokenTable";
import ShareProjectButton from "./share-project-button";
import { Dialog, DialogContent } from "./ui/dialog";
import ModalHeader from "./ui/modal-header";
import { FormField } from "./ui/form-field";
import { PrimaryButton } from "./ui/primary-button";
import { Switch } from "./ui/switch";
import { TabNavList, TabNavTrigger } from "./ui/tab-nav";
import { Tabs, TabsContent } from "./ui/tabs";

/*
 * Project settings: the Create-project modal's panel, fields and button, wider
 * because it also holds the API-tokens table. The design has no frame for this
 * dialog, so it is the redesign's vocabulary applied to the controls it had.
 *
 * The fields save on submit; the public toggle saves the moment it is flipped,
 * which is what lets the sharing link it controls appear and disappear with it.
 * Only a failed submit keeps the dialog open, so edits that did not save are
 * still there to retry.
 */

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
    const [name, setName] = useState(project.name || "");
    const [description, setDescription] = useState(project.description || "");
    const [isPublic, setIsPublic] = useState(project.public || false);
    const [isSaving, setIsSaving] = useState(false);
    const [activeTab, setActiveTab] = useState("general");

    /*
     * The dialog stays mounted between openings, so the tab it was left on would
     * otherwise still be showing the next time it opens. Settings starts on
     * General; the tokens tab is somewhere you go, not somewhere you resume.
     */
    useEffect(() => {
        if (open) setActiveTab("general");
    }, [open]);

    /*
     * Reset the form when the dialog moves to a *different* project, keyed on the
     * id rather than the object. The toggle below saves as it is flipped, which
     * refreshes the project and hands this component a new object; keying on the
     * object would make that refresh overwrite whatever the user had typed.
     */
    useEffect(() => {
        setName(project.name || "");
        setDescription(project.description || "");
        setIsPublic(project.public || false);
    }, [project.id, project.name, project.description, project.public]);

    /*
     * The public toggle saves on its own, so the sharing link it controls appears
     * and disappears with it rather than waiting for the form to be submitted.
     *
     * It writes only the flag: the name and description it sends are the *saved*
     * ones, not what is currently in the fields, so flipping the switch never
     * quietly commits half-typed text. The switch moves first and rolls back if
     * the write fails, so it always shows what is actually stored.
     */
    const handlePublicChange = async (next: boolean) => {
        setIsPublic(next);
        try {
            await updateProject(project.id, {
                name: project.name,
                description: project.description,
                public: next,
            });
            onProjectUpdated();
        } catch (error) {
            console.error("Error updating project visibility:", error);
            setIsPublic(!next);
            toast.error("Failed to change project visibility");
        }
    };

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
            onOpenChange(false);
        } catch (error) {
            // Left open on failure, so the edits that failed to save are still
            // there to retry rather than being discarded.
            console.error("Error updating project:", error);
            toast.error("Failed to update project settings");
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent
                hideClose
                className="max-w-[720px] gap-0 rounded-none border-2 border-black bg-cc-background p-0 shadow-dialog"
            >
                <ModalHeader title="Project settings" />

                <Tabs
                    value={activeTab}
                    onValueChange={setActiveTab}
                    className="w-full"
                >
                    <TabNavList className="px-6 sm:px-10">
                        <TabNavTrigger value="general">General</TabNavTrigger>
                        <TabNavTrigger value="tokens">API Tokens</TabNavTrigger>
                    </TabNavList>

                    <TabsContent
                        value="general"
                        className="mt-0 px-6 py-8 sm:px-10 sm:py-10"
                    >
                        <form
                            className="flex flex-col gap-7"
                            onSubmit={(event) => {
                                event.preventDefault();
                                handleSave();
                            }}
                        >
                            <FormField
                                id="name"
                                label="Name"
                                placeholder="Name"
                                required
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                            />

                            <FormField
                                id="description"
                                label="Description"
                                placeholder="Description"
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                            />

                            <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
                                <Switch
                                    id="isPublic"
                                    checked={isPublic}
                                    onCheckedChange={handlePublicChange}
                                />
                                <label
                                    htmlFor="isPublic"
                                    className="type-mono-regular type-field cursor-pointer text-cc-white"
                                >
                                    Make project public
                                </label>
                                <p className="type-mono-regular type-row-meta text-cc-gray">
                                    (enables public sharing link)
                                </p>
                            </div>

                            {/* Appears and disappears with the toggle above,
                                which saves itself. */}
                            <ShareProjectButton
                                projectId={project.id}
                                isPublic={isPublic}
                                trigger="labelled"
                            />

                            <div className="flex pt-4">
                                <PrimaryButton
                                    type="submit"
                                    disabled={isSaving || !name.trim()}
                                >
                                    {isSaving && (
                                        <Loader2 className="size-4 animate-spin motion-reduce:animate-none" />
                                    )}
                                    {isSaving ? "Saving..." : "Save changes"}
                                </PrimaryButton>
                            </div>
                        </form>
                    </TabsContent>

                    {/* Not redesigned yet — the table keeps its current look. */}
                    <TabsContent
                        value="tokens"
                        className="mt-0 px-6 py-8 sm:px-10 sm:py-10"
                    >
                        <ProjectTokensTable projectId={project.id} />
                    </TabsContent>
                </Tabs>
            </DialogContent>
        </Dialog>
    );
}
