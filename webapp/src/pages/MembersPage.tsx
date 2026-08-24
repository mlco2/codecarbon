import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import useSWR, { mutate } from "swr";
import { toast } from "sonner";
import { z } from "zod";

import ErrorMessage from "@/components/error-message";
import Loader from "@/components/loader";
import MemberRow from "@/components/member-row";
import { FormField } from "@/components/ui/form-field";
import { PrimaryButton } from "@/components/ui/primary-button";
import {
    Table,
    TableBody,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";

import { addOrganizationUser } from "@/api/organizations";
import { Organization, OrganizationUser } from "@/api/schemas";
import { fetcher } from "@/api/swr";

/*
 * The Members page, in its empty, populated and submitting states.
 *
 * The Projects page's shell, which it is a sibling of; what differs is the
 * action — a form on the page rather than a dialog, since the API takes a
 * single email address.
 *
 * The design's frames still draw the older in-page navigation; that lives in
 * `SidebarRail` and `AccountMenu` now and is not rebuilt here.
 */
export default function MembersPage() {
    const { organizationId } = useParams<{ organizationId: string }>();

    const [email, setEmail] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [isInviting, setIsInviting] = useState(false);

    /*
     * The breadcrumb's organization name, fetched as the other redesigned pages
     * fetch it, with the name the navigation already cached as the fallback so
     * the crumb never flashes a bare id.
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

    const membersKey = `/organizations/${organizationId}/users`;
    const {
        data: members,
        error: fetchError,
        isLoading,
    } = useSWR<OrganizationUser[]>(membersKey, fetcher);

    const emailSchema = z.string().email("Please enter a valid email address");

    async function handleInvite(event: React.FormEvent) {
        event.preventDefault();

        const parsed = emailSchema.safeParse(email.trim());
        if (!parsed.success) {
            setError(parsed.error.errors[0].message);
            return;
        }
        setError(null);
        setIsInviting(true);

        try {
            await addOrganizationUser(organizationId!, parsed.data);
            /* The design's success alert names the address it went to. */
            toast.success(`Invite sent to ${parsed.data}`);
            setEmail("");
            await mutate(membersKey);
        } catch (err) {
            const message =
                err instanceof Error ? err.message : "Failed to invite member";
            /* Kept on the field as well as in the toast: the toast goes away,
               and the address that failed is still sitting in the input. */
            setError(message);
            toast.error(message);
        } finally {
            setIsInviting(false);
        }
    }

    if (isLoading) {
        return <Loader />;
    }

    if (fetchError || !members) {
        return <ErrorMessage />;
    }

    const sortedMembers = [...members].sort((a, b) =>
        (a.name || a.email)
            .toLowerCase()
            .localeCompare((b.name || b.email).toLowerCase()),
    );
    const hasMembers = sortedMembers.length > 0;

    return (
        /* The Global dashboard's content column: one scrolling region whose
           padding is the single horizontal gutter for everything inside it. */
        <div className="flex h-full min-h-0 flex-col overflow-y-auto bg-cc-page-background px-5 pb-10 pt-4 sm:px-10 lg:px-20 lg:pb-8 lg:pt-5">
            {/* The parent crumb hovers to white rather than to the design's
                button-hover green, which is the colour of the current crumb
                beside it — hovering should not make a link look like the page
                you are already on. */}
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
                <span className="text-cc-button-hover">Members</span>
            </nav>

            <header className="border-b border-cc-rule pb-5 lg:pb-6">
                <h1 className="type-display type-page-title min-w-0 text-cc-white">
                    Members
                </h1>
            </header>

            {/*
             * A real form, so Enter submits and the browser validates the
             * address before the request does. The button aligns with the
             * field's control rather than with the label above it, which is why
             * the row is bottom-aligned until it wraps.
             */}
            <form
                onSubmit={handleInvite}
                className="flex flex-wrap items-end gap-4 border-b border-cc-rule py-6"
            >
                <FormField
                    id="member-email"
                    label="Invite via email"
                    type="email"
                    placeholder="name@example.com"
                    value={email}
                    onChange={(event) => {
                        setEmail(event.target.value);
                        setError(null);
                    }}
                    disabled={isInviting}
                    aria-invalid={error ? true : undefined}
                    aria-describedby={error ? "member-email-error" : undefined}
                    containerClassName="w-full max-w-[466px]"
                />
                <PrimaryButton
                    type="submit"
                    ringOffset="page"
                    /* Nothing to send until an address is typed, and the second
                       press while one is in flight would send it twice. */
                    disabled={isInviting || email.trim().length === 0}
                    className="h-control shrink-0"
                >
                    {isInviting ? (
                        <>
                            {/* The design shows the spinner alone; the label it
                                replaces still has to reach a screen reader. */}
                            <Loader2 className="size-5 animate-spin motion-reduce:animate-none" />
                            <span className="sr-only">Sending invite…</span>
                        </>
                    ) : (
                        "Invite"
                    )}
                </PrimaryButton>
                {error && (
                    <p
                        id="member-email-error"
                        role="alert"
                        className="type-mono-regular type-row-meta w-full text-cc-lime"
                    >
                        {error}
                    </p>
                )}
            </form>

            {hasMembers ? (
                /* The design leaves more air between the invite form's rule and
                   the column heading than the heading's own padding gives. */
                <Table containerClassName="pt-6">
                    {/*
                     * The design labels this one column and no other, so the
                     * header row carries a single heading and the status and
                     * actions columns stay unlabelled. `TableHead` sets its own
                     * weight and colour, which the design's display face
                     * overrides here.
                     */}
                    <TableHeader>
                        <TableRow className="border-cc-rule hover:bg-transparent">
                            <TableHead className="type-display type-column-head h-auto px-0 py-3 font-bold text-cc-white opacity-50">
                                Name
                            </TableHead>
                            <TableHead className="h-auto px-4 py-3">
                                <span className="sr-only">Role</span>
                            </TableHead>
                            <TableHead className="h-auto w-px p-0">
                                <span className="sr-only">Actions</span>
                            </TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {sortedMembers.map((member) => (
                            <MemberRow key={member.id} member={member} />
                        ))}
                    </TableBody>
                </Table>
            ) : (
                /*
                 * The design centres this line in whatever the frame has left
                 * below the form; here it takes the space the column has over
                 * and centres within that, with a minimum so it still reads as
                 * an empty area when the viewport is short.
                 *
                 * The line is set in Inter in the design, alone among every
                 * node in the file — plainly a default rather than intent, so it
                 * takes the mono face the rest of the redesign uses, matching
                 * the Projects page's equivalent line.
                 */
                <div className="flex min-h-64 flex-1 flex-col items-center justify-center px-4 py-12 text-center">
                    <p className="type-mono-medium type-field text-cc-white">
                        You have no members invited yet...
                    </p>
                </div>
            )}
        </div>
    );
}
