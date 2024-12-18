"use client";

import {
    Breadcrumb,
    BreadcrumbItem,
    BreadcrumbLink,
    BreadcrumbList,
    BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { usePathname } from "next/navigation";
import React from "react";

export default function AutoBreadcrumb() {
    const pathname = usePathname();
    const pathSegments = pathname
        .split("/")
        .filter((segment) => segment !== "");

    return (
        <Breadcrumb>
            <BreadcrumbList>
                {pathSegments.length > 1 &&
                    pathSegments.map((segment, index) => {
                        const isLast = index === pathSegments.length - 1;

                        const href = `/${pathSegments.slice(0, index + 1).join("/")}`;
                        const title =
                            segment.charAt(0).toUpperCase() + segment.slice(1);

                        return (
                            <React.Fragment key={href}>
                                <BreadcrumbItem>
                                    <BreadcrumbLink href={href}>
                                        {title}
                                    </BreadcrumbLink>
                                </BreadcrumbItem>
                                {!isLast && <BreadcrumbSeparator />}
                            </React.Fragment>
                        );
                    })}
            </BreadcrumbList>
        </Breadcrumb>
    );
}
