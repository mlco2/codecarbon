import {
    Breadcrumb,
    BreadcrumbItem,
    BreadcrumbLink,
    BreadcrumbList,
    BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import React from "react";

export default function BreadcrumbHeader({
    pathSegments,
}: {
    pathSegments: {
        title: string;
        href: string | null;
    }[];
}) {
    return (
        <Breadcrumb>
            <BreadcrumbList>
                {pathSegments.map((segment, index) => {
                    const isLast = index === pathSegments.length - 1;
                    const title = segment.title;
                    const href = segment.href;
                    return (
                        <React.Fragment key={href}>
                            <BreadcrumbItem>
                                {href ? (
                                    <BreadcrumbLink href={href}>
                                        {title}
                                    </BreadcrumbLink>
                                ) : (
                                    <span>{title}</span>
                                )}
                            </BreadcrumbItem>
                            {!isLast && <BreadcrumbSeparator />}
                        </React.Fragment>
                    );
                })}
            </BreadcrumbList>
        </Breadcrumb>
    );
}
