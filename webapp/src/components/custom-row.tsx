"use client";

import { Settings } from "lucide-react";
import { useRouter } from "next/navigation";
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
  key,
  firstColumn,
  secondColumn,
  href,
}: {
  key: string;
  firstColumn: string;
  secondColumn: string;
  href?: string;
}) {
  const router = useRouter();
  const cellClassName = `font-medium ${href && "hover:cursor-pointer"} `;

  return (
    <TableRow key={key}>
      <TableCell
        onClick={() => href && router.push(href)}
        className={`text-left ${cellClassName}`}
      >
        {firstColumn}
      </TableCell>
      <TableCell
        onClick={() => href && router.push(href)}
        className={`text-left ${cellClassName}`}
      >
        {secondColumn}
      </TableCell>
      <TableCell className="text-right w-6">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="rounded-full">
              <span className="sr-only">Toggle project settings</span>
              <Settings className="w-5 h-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem disabled>Settings</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem disabled>Delete</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </TableCell>
    </TableRow>
  );
}
