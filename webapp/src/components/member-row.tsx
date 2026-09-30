import { OrganizationUser } from "@/api/schemas";
import { cn } from "@/helpers/utils";
import { MoreVertIcon } from "./icons/more-vert-icon";
import { UserSingleAimIcon } from "./icons/user-single-aim-icon";
import { DropdownMenu, DropdownMenuTrigger } from "./ui/dropdown-menu";
import { MenuItem, MenuPanel } from "./ui/menu";
import { TableCell, TableRow } from "./ui/table";

/*
 * One member of the organization: an avatar, their name and email, their
 * standing in it, and a menu of the actions that apply to them.
 *
 * Unlike a project row this is not a link — there is no member page to open —
 * so nothing lights on hover and the overflow menu is its only control.
 *
 * The avatar is decorative: no API field can fill the design's photo circle, so
 * it renders the design's member glyph and the name beside it is the identity.
 */

/*
 * The trigger's padding, and the gap its menu keeps from the glyph. Radix
 * anchors to the trigger's whole box, so both are cancelled to bring the panel
 * back to the dots. Same values as a project row's, because it is the same
 * control.
 */
const TRIGGER_INSET = 20;
const MENU_GAP = 4;

export default function MemberRow({
    member,
    onDelete,
}: Readonly<{
    member: OrganizationUser;
    /** Omitted for anyone who may not remove this member; the menu then has
        nothing in it and the trigger is not rendered at all. */
    onDelete?: () => void;
}>) {
    /* The API's name can come back empty; the email is the only field always
       present, so it becomes the row's title when there is nothing above it. */
    const name = member.name?.trim();

    return (
        <TableRow className="border-cc-rule hover:bg-transparent">
            <TableCell className="w-1/2 px-0 py-4 align-middle">
                <div className="flex items-center gap-3">
                    <span
                        aria-hidden="true"
                        className="flex size-12 shrink-0 items-center justify-center rounded-full bg-cc-dark-gray text-cc-lime"
                    >
                        <UserSingleAimIcon className="size-8" />
                    </span>
                    {/* Wraps rather than overflows: an email address is long
                        and a narrow screen has to hold it. */}
                    <div className="flex min-w-0 flex-col gap-1.5">
                        {name && (
                            <span className="type-mono-medium type-member-name break-words text-cc-white">
                                {name}
                            </span>
                        )}
                        <span
                            className={cn(
                                "type-mono-medium break-all text-cc-white",
                                name ? "type-member-meta" : "type-member-name",
                            )}
                        >
                            {member.email}
                        </span>
                    </div>
                </div>
            </TableCell>

            {/*
             * The design's status note. It reads "(Invited unnaccepted yet)",
             * which nothing in the API can tell us — adding a member subscribes
             * an existing account immediately, so there is no pending state. The
             * slot instead carries the one thing the membership does record,
             * which is whether they administer the organization.
             */}
            <TableCell className="px-4 py-4 align-middle">
                {member.is_admin && (
                    <span className="type-mono-medium type-row-meta whitespace-nowrap text-cc-button-hover">
                        (Admin)
                    </span>
                )}
            </TableCell>

            {/* Only as wide as its trigger, and empty when there is nothing
                to offer — a disabled control would only advertise an action
                the viewer cannot take. */}
            <TableCell className="w-px p-0 align-middle">
                {onDelete && (
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <button
                                type="button"
                                className="flex cursor-pointer items-center p-5 text-cc-white outline-none transition-colors hover:text-cc-button-hover focus-visible:ring-2 focus-visible:ring-cc-lime data-[state=open]:text-cc-button-hover motion-reduce:transition-none"
                            >
                                <span className="sr-only">
                                    {`Actions for ${name || member.email}`}
                                </span>
                                <MoreVertIcon className="size-6" />
                            </button>
                        </DropdownMenuTrigger>
                        {/*
                         * The design fills this menu with "Resend invite" and a
                         * "Settings" entry, neither of which has an endpoint
                         * behind it — there is no pending invitation to resend
                         * and no membership field to edit. Removal is the one
                         * action the API supports, so it is the one row here.
                         */}
                        <MenuPanel
                            align="end"
                            sideOffset={MENU_GAP - TRIGGER_INSET}
                            alignOffset={TRIGGER_INSET}
                        >
                            <MenuItem onSelect={onDelete}>Delete</MenuItem>
                        </MenuPanel>
                    </DropdownMenu>
                )}
            </TableCell>
        </TableRow>
    );
}
