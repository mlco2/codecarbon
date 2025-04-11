"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { encryptProjectId } from "@/utils/crypto";
import copy from "copy-to-clipboard";
import { CheckIcon, CopyIcon, LockIcon, Share2Icon } from "lucide-react";
import { useEffect, useState } from "react";
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
    const [encryptedId, setEncryptedId] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isOpen, setIsOpen] = useState(false);
    const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || window.location.origin;

    useEffect(() => {
        const fetchEncryptedId = async () => {
            if (isPublic && projectId && isOpen && !encryptedId) {
                try {
                    setIsLoading(true);
                    const encrypted = await encryptProjectId(projectId);
                    setEncryptedId(encrypted);
                } catch (error) {
                    console.error("Failed to encrypt project ID:", error);
                    toast.error("Failed to generate secure sharing link");
                } finally {
                    setIsLoading(false);
                }
            }
        };

        fetchEncryptedId();
    }, [projectId, isPublic, isOpen, encryptedId]);

    const publicUrl = encryptedId
        ? `${baseUrl}/public/projects/${encryptedId}`
        : "";

    const copyToClipboard = () => {
        if (isLoading || !publicUrl) return;

        try {
            copy(publicUrl);
            setCopied(true);
            toast.success("Secure link copied to clipboard");
            setTimeout(() => setCopied(false), 2000);
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
            <Popover onOpenChange={setIsOpen} open={isOpen}>
                <PopoverTrigger asChild>
                    <Button
                        variant="outline"
                        size="icon"
                        className="flex items-center gap-2 rounded-full"
                    >
                        <Share2Icon className="h-4 w-4" />
                    </Button>
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
                                value={isLoading ? "..." : publicUrl}
                                className="flex-1"
                            />
                            <Button
                                size="icon"
                                onClick={copyToClipboard}
                                disabled={isLoading || !publicUrl}
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
