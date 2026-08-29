import { LockIcon } from "./icons/lock-icon";
import { ShareIcon } from "./icons/share-icon";
import { Badge } from "./ui/badge";

/*
 * Whether a project is visible to anyone with its link, shown beside its name.
 *
 * Its own module rather than an export of the project dashboard, so the page
 * heading can show it without importing from the panels below it.
 *
 * The glyphs are the redesign's own; the pill around them is still the badge as
 * it was. They are drawn a little larger than the 12px the old icons used —
 * pixel-art strokes need the room to stay legible at this size.
 */
export default function ProjectVisibilityBadge({
    isPublic,
}: Readonly<{ isPublic: boolean }>) {
    return isPublic ? (
        <Badge
            variant="default"
            className="flex items-center gap-1 bg-primary/20 text-primary hover:bg-primary/20"
        >
            <ShareIcon className="size-4 shrink-0" />
            Public
        </Badge>
    ) : (
        <Badge
            variant="default"
            className="flex items-center gap-1 bg-destructive/20 text-destructive-foreground hover:bg-destructive/20"
        >
            <LockIcon className="size-4 shrink-0" />
            Private
        </Badge>
    );
}
