import { Button } from "@/components/ui/button";
import { Download, Loader2 } from "lucide-react";
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
                    <Button
                        variant="ghost"
                        size="icon"
                        aria-label="Download CSV export"
                        disabled={isExporting || isDisabled}
                        onClick={handleDownload}
                    >
                        {isExporting ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <Download className="h-4 w-4" />
                        )}
                    </Button>
                </TooltipTrigger>
                <TooltipContent>
                    <p>Download .csv export</p>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    );
}
