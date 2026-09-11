import { ShareIcon } from "@/components/icons/share-icon";
import { IconButton } from "@/components/ui/icon-button";
import { SecondaryButton } from "@/components/ui/secondary-button";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import copy from "copy-to-clipboard";
import { CheckIcon, CopyIcon } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";

interface ShareProjectButtonProps {
    projectId: string;
    isPublic: boolean;
    /*
     * How the control presents itself. `icon` is the round icon button the
     * project dashboard has always shown; `labelled` is the redesign's outlined
     * "Copy link" button, used where the control sits in a form beside the
     * setting that produces the link. Both open the same panel.
     */
    trigger?: "icon" | "labelled";
}

export default function ShareProjectButton({
    projectId,
    isPublic,
    trigger = "icon",
}: ShareProjectButtonProps) {
    const [copied, setCopied] = useState(false);
    const copyTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const baseUrl = import.meta.env.VITE_BASE_URL || window.location.origin;

    useEffect(() => {
        return () => {
            if (copyTimerRef.current) clearTimeout(copyTimerRef.current);
        };
    }, []);

    const publicUrl = `${baseUrl}/public/projects/${projectId}`;

    const copyToClipboard = () => {
        try {
            copy(publicUrl);
            setCopied(true);
            toast.success("Public link copied to clipboard");
            copyTimerRef.current = setTimeout(() => setCopied(false), 2000);
        } catch (error) {
            console.error("Failed to copy to clipboard:", error);
            toast.error("Failed to copy link to clipboard");
        }
    };

    if (!isPublic) {
        return null;
    }

    return (
        <div className="flex items-center gap-2">
            <Popover>
                <PopoverTrigger asChild>
                    {trigger === "labelled" ? (
                        <SecondaryButton>
                            <ShareIcon className="size-5 shrink-0" />
                            Copy link
                        </SecondaryButton>
                    ) : (
                        <IconButton aria-label="Share project">
                            <ShareIcon className="size-6" />
                        </IconButton>
                    )}
                </PopoverTrigger>
                <PopoverContent className="w-80 p-5" align="end">
                    <div className="flex flex-col gap-4">
                        <div className="flex flex-col gap-1">
                            <h4 className="type-mono-medium type-field text-cc-white">
                                Share this project
                            </h4>
                            <p className="type-mono-medium type-row-meta text-cc-gray">
                                Anyone with this link can view this
                                project&apos;s emissions data without
                                authentication.
                            </p>
                        </div>
                        <div className="flex items-center gap-2">
                            {/* The link is read, not typed into, so it is text
                                rather than a field. */}
                            <code className="type-mono-regular type-row-meta min-w-0 flex-1 break-all text-cc-text-input-gray">
                                {publicUrl}
                            </code>
                            <IconButton
                                aria-label="Copy share link"
                                onClick={copyToClipboard}
                            >
                                {copied ? (
                                    <CheckIcon className="size-5" />
                                ) : (
                                    <CopyIcon className="size-5" />
                                )}
                            </IconButton>
                        </div>
                    </div>
                </PopoverContent>
            </Popover>
        </div>
    );
}
