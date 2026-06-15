import { Settings } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { TableCell, TableRow } from "./ui/table";

export default function CustomRow({
    rowKey,
    firstColumn,
    secondColumn,
    href,
    hrefSettings,
    onDelete = async () => {},
    deleteDisabled = true,
    settingsDisabled = true,
}: {
    rowKey: string;
    firstColumn: string;
    secondColumn: string;
    href?: string;
    hrefSettings?: string;
    onDelete?: () => Promise<void>;
    deleteDisabled?: boolean;
    settingsDisabled?: boolean;
}) {
    const navigate = useNavigate();
    const cellClassName = `font-medium ${href ? "hover:cursor-pointer" : ""} `;

    const handleCellKeyDown = (e: React.KeyboardEvent) => {
        if (href && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            navigate(href);
        }
    };

    return (
        <TableRow key={rowKey}>
            <TableCell
                onClick={() => href && navigate(href)}
                onKeyDown={handleCellKeyDown}
                tabIndex={href ? 0 : undefined}
                role={href ? "link" : undefined}
                className={`text-left ${cellClassName}`}
            >
                {firstColumn}
            </TableCell>
            <TableCell
                onClick={() => href && navigate(href)}
                onKeyDown={handleCellKeyDown}
                tabIndex={href ? 0 : undefined}
                role={href ? "link" : undefined}
                className={`text-left ${cellClassName}`}
            >
                {secondColumn}
            </TableCell>
            <TableCell className="text-right w-6">
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="rounded-full"
                        >
                            <span className="sr-only">
                                Toggle project settings
                            </span>
                            <Settings className="w-5 h-5" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent>
                        <DropdownMenuItem
                            disabled={settingsDisabled}
                            onClick={() =>
                                hrefSettings &&
                                !settingsDisabled &&
                                navigate(hrefSettings)
                            }
                        >
                            Settings
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                            onClick={onDelete}
                            disabled={deleteDisabled}
                        >
                            Delete
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </TableCell>
        </TableRow>
    );
}
