import { Loader2 } from "lucide-react";
import { DownloadIcon } from "@/components/icons/download-icon";
import { useState } from "react";
import { toast } from "sonner";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";

interface ExportCsvButtonProps {
    onDownload: () => Promise<void>;
    isDisabled?: boolean;
    loadingMessage?: string;
    successMessage?: string;
    errorMessage?: string;
}

export function ExportCsvButton({
    onDownload,
    isDisabled = false,
    loadingMessage = "Exporting data...",
    successMessage = "Data exported successfully",
    errorMessage = "Failed to export data",
}: ExportCsvButtonProps) {
    const [isExporting, setIsExporting] = useState(false);

    const handleDownload = () => {
        setIsExporting(true);
        toast.promise(
            (async () => {
                await onDownload();
                setIsExporting(false);
            })(),
            {
                loading: loadingMessage,
                success: successMessage,
                error: errorMessage,
            },
        );
    };

    return (
        <TooltipProvider>
            <Tooltip>
                <TooltipTrigger asChild>
                    <button
                        type="button"
                        aria-label="Download CSV export"
                        disabled={isExporting || isDisabled}
                        onClick={handleDownload}
                        className="cursor-pointer text-cc-gray outline-none transition-colors hover:text-cc-button-hover focus-visible:ring-2 focus-visible:ring-cc-lime disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:text-cc-gray motion-reduce:transition-none"
                    >
                        {isExporting ? (
                            <Loader2 className="size-5 animate-spin motion-reduce:animate-none" />
                        ) : (
                            <DownloadIcon className="size-5" />
                        )}
                    </button>
                </TooltipTrigger>
                <TooltipContent>
                    <p>Download .csv export</p>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    );
}
