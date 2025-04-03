"use client";

import { Button } from "@/components/ui/button";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { Input } from "@/components/ui/input";
import { Share2Icon, CopyIcon, CheckIcon } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

interface ShareProjectButtonProps {
    projectId: string;
    isPublic: boolean;
}

export default function ShareProjectButton({
    projectId,
    isPublic,
}: ShareProjectButtonProps) {
    const [copied, setCopied] = useState(false);
    const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || window.location.origin;
    const publicUrl = `${baseUrl}/public/projects/${projectId}`;

    const copyToClipboard = () => {
        navigator.clipboard.writeText(publicUrl);
        setCopied(true);
        toast.success("Link copied to clipboard");
        setTimeout(() => setCopied(false), 2000);
    };

    if (!isPublic) {
        return null;
    }

    return (
        <Popover>
            <PopoverTrigger asChild>
                <Button variant="outline" className="flex items-center gap-2">
                    <Share2Icon className="h-4 w-4" />
                    Share Project
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80">
                <div className="space-y-4">
                    <h4 className="font-medium leading-none">
                        Share this project
                    </h4>
                    <p className="text-sm text-muted-foreground">
                        Anyone with this link can view this project&apos;s
                        emissions data.
                    </p>
                    <div className="flex space-x-2">
                        <Input readOnly value={publicUrl} className="flex-1" />
                        <Button size="icon" onClick={copyToClipboard}>
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
    );
}
