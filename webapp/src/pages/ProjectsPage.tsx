import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import useSWR from "swr";
import { toast } from "sonner";

import CreateProjectModal from "@/components/create-project-modal";
import DeleteProjectModal from "@/components/delete-project-modal";
import ErrorMessage from "@/components/error-message";
import Loader from "@/components/loader";
import ProjectRow from "@/components/project-row";
import ProjectSettingsModal from "@/components/project-settings-modal";
import { PlusIcon } from "@/components/icons/plus-icon";
import { PrimaryButton } from "@/components/ui/primary-button";
import { Table, TableBody } from "@/components/ui/table";

import { fetcher } from "@/api/swr";
import { deleteProject, getProjects } from "@/api/projects";
import { Organization, Project } from "@/api/schemas";
import { useModal } from "@/hooks/useModal";

/*
 * The Projects page, in its empty and populated states, which differ only in
 * where the primary action sits: centred in the empty area, or on the heading
 * row beside the title.
 *
 * The design's frames still draw the older in-page navigation; that lives in
 * `SidebarRail` and `AccountMenu` now and is not rebuilt here.
 *
 * A row's secondary text is the project's description — the design labels it
 * "Last updated on 02/02/24", and the API carries no timestamp.
 */
export default function ProjectsPage() {
    const { organizationId } = useParams<{ organizationId: string }>();

    const createModal = useModal();
    const settingsModal = useModal();
    const deleteModal = useModal();
    const [projectList, setProjectList] = useState<Project[]>([]);
    const [projectToEdit, setProjectToEdit] = useState<Project | null>(null);
    const [projectToDelete, setProjectToDelete] = useState<Project | null>(
        null,
    );

    /*
     * The breadcrumb's organization name. Fetched like the Global dashboard does,
     * with the name the navigation already cached as the fallback while the request
     * is in flight, so the crumb never flashes a bare id.
     */
    const { data: organization } = useSWR<Organization>(
        organizationId ? `/organizations/${organizationId}` : null,
        fetcher,
        { revalidateOnFocus: false },
    );
    let cachedOrganizationName: string | null = null;
    try {
        cachedOrganizationName = localStorage.getItem("organizationName");
    } catch {
        cachedOrganizationName = null;
    }
    const organizationName =
        organization?.name || cachedOrganizationName || organizationId!;

    const {
        data: projects,
        error,
        isLoading,
    } = useSWR<Project[]>(`/projects?organization=${organizationId}`, fetcher);

    useEffect(() => {
        if (projects) {
            setProjectList(projects);
        }
    }, [projects]);

    const refreshProjectList = async () => {
        const refreshed = await getProjects(organizationId!);
        setProjectList(refreshed || []);
    };

    const handleSettingsClick = (project: Project) => {
        setProjectToEdit(project);
        settingsModal.open();
    };

    const handleDeleteClick = (project: Project) => {
        setProjectToDelete(project);
        deleteModal.open();
    };

    const handleDeleteConfirm = async (projectId: string) => {
        try {
            await deleteProject(projectId);
            toast.success("Project deleted successfully");
            await refreshProjectList();
        } catch (error) {
            console.error("Error deleting project:", error);
            toast.error("Failed to delete project");
        }
    };

    if (isLoading) {
        return <Loader />;
    }

    if (error) {
        return <ErrorMessage />;
    }

    const sortedProjects = [...projectList].sort((a, b) =>
        a.name.toLowerCase().localeCompare(b.name.toLowerCase()),
    );
    const hasProjects = sortedProjects.length > 0;

    /* The same button in the design's two placements: on the heading row, and
       centred in the empty state. */
    const addProjectButton = (
        <PrimaryButton
            onClick={createModal.open}
            ringOffset="page"
            className="shrink-0 gap-1"
        >
            <PlusIcon className="size-5 shrink-0" />
            Add a project
        </PrimaryButton>
    );

    return (
        /* The Global dashboard's content column: one scrolling region whose
           padding is the single horizontal gutter for everything inside it. */
        <div className="flex h-full min-h-0 flex-col overflow-y-auto bg-cc-page-background px-5 pb-10 pt-4 sm:px-10 lg:px-20 lg:pb-8 lg:pt-5">
            {/* The parent crumb hovers to white rather than to the design's
                button-hover green, which is the colour of the current crumb beside
                it — hovering should not make a link look like the page you are
                already on. */}
            <nav
                aria-label="Breadcrumb"
                className="type-mono-medium type-breadcrumb pb-8 lg:pb-16"
            >
                <Link
                    to={`/${organizationId}`}
                    className="text-cc-breadcrumb-gray transition-colors hover:text-cc-white motion-reduce:transition-none"
                >
                    {organizationName}/
                </Link>
                <span className="text-cc-button-hover">Projects</span>
            </nav>

            {/* The action joins the heading only when there are projects; the
                empty state centres it instead. */}
            <header className="flex flex-wrap items-center justify-between gap-x-6 gap-y-4 border-b border-cc-rule pb-5 lg:pb-6">
                <h1 className="type-display type-page-title min-w-0 text-cc-white">
                    Projects
                </h1>
                {hasProjects && addProjectButton}
            </header>

            {hasProjects ? (
                <Table>
                    <TableBody>
                        {sortedProjects.map((project) => (
                            <ProjectRow
                                key={project.id}
                                project={project}
                                href={`/${organizationId}/projects/${project.id}`}
                                onSettings={() => handleSettingsClick(project)}
                                onDelete={() => handleDeleteClick(project)}
                            />
                        ))}
                    </TableBody>
                </Table>
            ) : (
                /*
                 * The design gives the empty region a fixed 525px height purely to
                 * centre its contents in the frame; here it takes the space the
                 * column has left over and centres within that, with a minimum so
                 * it still reads as an empty area when the viewport is short.
                 */
                <div className="flex min-h-64 flex-1 flex-col items-center justify-center gap-5 px-4 py-12 text-center">
                    {addProjectButton}
                    <p className="type-mono-medium type-field text-cc-white">
                        You have no projects added yet...
                    </p>
                </div>
            )}

            <CreateProjectModal
                organizationId={organizationId!}
                isOpen={createModal.isOpen}
                onClose={createModal.close}
                onProjectCreated={refreshProjectList}
            />

            {/*
             * Settings opens in place rather than navigating away. The project
             * dashboard's own settings control already opens this same modal, so
             * the row menu now behaves the way the rest of the app does, and acting
             * on a row no longer costs you the list you were working in. The row
             * already holds the whole project, so nothing is refetched.
             */}
            {projectToEdit && (
                <ProjectSettingsModal
                    open={settingsModal.isOpen}
                    onOpenChange={settingsModal.setIsOpen}
                    project={projectToEdit}
                    onProjectUpdated={refreshProjectList}
                />
            )}

            {projectToDelete && (
                <DeleteProjectModal
                    open={deleteModal.isOpen}
                    onOpenChange={deleteModal.setIsOpen}
                    projectName={projectToDelete.name}
                    projectId={projectToDelete.id}
                    onDelete={handleDeleteConfirm}
                />
            )}
        </div>
    );
}
