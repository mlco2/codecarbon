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
 * Everything here, the public toggle included, saves on submit; the dialog then
 * stays open, so the sharing link the toggle enables appears next to the save
 * button rather than behind a second trip into settings.
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
    /*
     * What visibility is actually stored, which is what the sharing link below
     * follows. Tracked here rather than read from the prop because a parent may
     * hold the project it opened the dialog with and not re-pass it after a
     * save.
     */
    const [savedIsPublic, setSavedIsPublic] = useState(project.public || false);
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
     * Reset the form when the project this dialog is editing changes, including
     * the refresh that follows a save. Keyed on the fields rather than the
     * object, which is a new one on every refresh.
     */
    useEffect(() => {
        setName(project.name || "");
        setDescription(project.description || "");
        setIsPublic(project.public || false);
        setSavedIsPublic(project.public || false);
    }, [project.id, project.name, project.description, project.public]);

    const handleSave = async () => {
        setIsSaving(true);
        try {
            await updateProject(project.id, {
                name,
                description,
                public: isPublic,
            });
            setSavedIsPublic(isPublic);
            toast.success("Project settings updated successfully");
            // Kept open: the sharing link a just-enabled project gains appears
            // beside the button that was clicked, ready to copy.
            onProjectUpdated();
        } catch (error) {
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
                                    onCheckedChange={setIsPublic}
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

                            <div className="flex flex-wrap items-center justify-between gap-4 pt-4">
                                <PrimaryButton
                                    type="submit"
                                    disabled={isSaving || !name.trim()}
                                >
                                    {isSaving && (
                                        <Loader2 className="size-4 animate-spin motion-reduce:animate-none" />
                                    )}
                                    {isSaving ? "Saving..." : "Save changes"}
                                </PrimaryButton>

                                {/* Follows the *saved* visibility, not the
                                    toggle: there is no link to copy until the
                                    project is actually public. */}
                                <ShareProjectButton
                                    projectId={project.id}
                                    isPublic={savedIsPublic}
                                    trigger="labelled"
                                />
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
