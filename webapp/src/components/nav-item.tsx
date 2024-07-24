import Link from "next/link";

export default function NavItem({
  href,
  isSelected,
  icon,
  children,
  paddingY = 3,
}: {
  href: string;
  isSelected: boolean;
  icon?: React.ReactNode;
  children: React.ReactNode;
  paddingY?: number;
}) {
  return (
    <Link
      href={href}
      className={`flex items-center gap-3 rounded-md py-${paddingY} text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground ${
        isSelected
          ? "text-primary rounded-full"
          : "text-muted-foreground hover:text-white"
      }`}
    >
      {icon}
      <span>{children}</span>
    </Link>
  );
}
