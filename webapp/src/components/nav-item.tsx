import { Button } from "./ui/button";

export default function NavItem({
    isSelected,
    onClick,
    icon,
    children,
    paddingY = 3,
}: {
    isSelected: boolean;
    onClick?: () => void;
    icon?: React.ReactNode;
    children: React.ReactNode;
    paddingY?: number;
}) {
    return (
        <Button
            variant={`ghost`}
            onClick={onClick}
            className={`w-full flex justify-start gap-3 rounded-md py-${paddingY} text-sm font-medium transition-colors hover:bg-accent text-left ${
                isSelected
                    ? "text-primary hover:text-primary"
                    : "text-muted-foreground hover:text-accent-foreground hover:text-white"
            }`}
        >
            {icon}
            <span>{children}</span>
        </Button>
    );
}
