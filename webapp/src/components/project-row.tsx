import { Link } from "react-router-dom";

import { Project } from "@/api/schemas";
import { cn } from "@/helpers/utils";
import { MoreVertIcon } from "./icons/figma-icons";
import { DropdownMenu, DropdownMenuTrigger } from "./ui/dropdown-menu";
import { MenuItem, MenuPanel } from "./ui/menu";
import { TableCell, TableRow } from "./ui/table";

/*
 * One project in the list: its name, its secondary text, and a menu of the
 * actions that apply to it.
 *
 * The name and the secondary text are both links to the project, and each fills
 * its cell — the row's vertical padding is on the links, so the whole height and
 * width of a cell is a click target rather than just the glyphs.
 *
 * The two light together on hover, because they are one item rather than two
 * independently hoverable cells. The actions cell is excluded from that: its
 * trigger is a small glyph in a padded cell, so if the cell lit the row along
 * with it there would be no way to tell whether the pointer is on the button or
 * merely near it. The trigger keeps its own hover, and that is the only thing
 * reporting its hitbox — which is also why an open menu lights the button alone.
 *
 * Focus stays per-control, since focus really is on one thing at a time.
 */

/** Lets the row's hover exclude the actions cell. */
const ACTIONS_CELL = "project-row-actions";

/*
 * The trigger's padding, and the gap its menu keeps from the glyph. Radix anchors
 * a menu to the trigger's box — the whole hit area — so cancelling that padding on
 * both axes anchors the panel to the dots themselves, and enlarging the hit area
 * no longer pushes the menu away from what opened it.
 */
const TRIGGER_INSET = 20;
const MENU_GAP = 4;

const CELL_LINK =
    "type-mono-medium block break-words py-5 text-cc-white outline-none transition-colors " +
    "group-[:hover:not(:has(.project-row-actions:hover))]:text-cc-button-hover " +
    "focus-visible:ring-2 focus-visible:ring-cc-lime lg:py-6 motion-reduce:transition-none";

export default function ProjectRow({
    project,
    href,
    onSettings,
    onDelete,
}: Readonly<{
    project: Project;
    href: string;
    onSettings: () => void;
    onDelete: () => void;
}>) {
    return (
        <TableRow className="group border-cc-rule hover:bg-transparent">
            {/* The name takes half the table, which is what starts the secondary
                text at its own column. */}
            <TableCell className="w-1/2 p-0 align-middle">
                <Link
                    to={href}
                    className={cn(CELL_LINK, "type-row-title pr-4")}
                >
                    {project.name}
                </Link>
            </TableCell>

            <TableCell className="p-0 align-middle">
                {project.description && (
                    <Link
                        to={href}
                        aria-label={`${project.name} — open project`}
                        className={cn(CELL_LINK, "type-row-meta px-4")}
                    >
                        {project.description}
                    </Link>
                )}
            </TableCell>

            {/* Only as wide as its trigger. */}
            <TableCell className={cn(ACTIONS_CELL, "w-px p-0 align-middle")}>
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <button
                            type="button"
                            className="flex cursor-pointer items-center p-5 text-cc-white outline-none transition-colors hover:text-cc-button-hover focus-visible:ring-2 focus-visible:ring-cc-lime data-[state=open]:text-cc-button-hover motion-reduce:transition-none"
                        >
                            <span className="sr-only">
                                {`Actions for ${project.name}`}
                            </span>
                            <MoreVertIcon className="size-6" />
                        </button>
                    </DropdownMenuTrigger>
                    <MenuPanel
                        align="end"
                        sideOffset={MENU_GAP - TRIGGER_INSET}
                        alignOffset={TRIGGER_INSET}
                    >
                        <MenuItem onSelect={onSettings}>Settings</MenuItem>
                        <MenuItem onSelect={onDelete}>Delete</MenuItem>
                    </MenuPanel>
                </DropdownMenu>
            </TableCell>
        </TableRow>
    );
}
