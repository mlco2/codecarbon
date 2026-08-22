import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SecondaryButton } from "@/components/ui/secondary-button";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import copy from "copy-to-clipboard";
import { CheckIcon, CopyIcon, Share2Icon } from "lucide-react";
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
                            <Share2Icon className="size-4 shrink-0" />
                            Copy link
                        </SecondaryButton>
                    ) : (
                        <Button
                            variant="outline"
                            size="icon"
                            aria-label="Share project"
                            className="flex items-center gap-2 rounded-full"
                        >
                            <Share2Icon className="h-4 w-4" />
                        </Button>
                    )}
                </PopoverTrigger>
                <PopoverContent className="w-80">
                    <div className="space-y-4">
                        <h4 className="font-medium leading-none">
                            Share this project
                        </h4>
                        <p className="text-sm text-muted-foreground">
                            Anyone with this link can view this project&apos;s
                            emissions data without authentication.
                        </p>
                        <div className="flex space-x-2">
                            <Input
                                readOnly
                                value={publicUrl}
                                className="flex-1"
                            />
                            <Button
                                size="icon"
                                aria-label="Copy share link"
                                onClick={copyToClipboard}
                            >
                                {copied ? (
                                    <CheckIcon className="h-4 w-4" />
                                ) : (
                                    <CopyIcon className="h-4 w-4" />
                                )}
                            </Button>
                        </div>
                    </div>
                </PopoverContent>
            </Popover>
        </div>
    );
}
