import { User } from "@/types/user";
import MembersList from "./members-list";
import BreadcrumbHeader from "@/components/breadcrumb";
import { Organization } from "@/types/organization";
import { fetchApi } from "@/utils/api";

export default async function MembersPage({
    params,
}: {
    params: Promise<{ organizationId: string }>;
}) {
    const { organizationId } = await params;

    const users: User[] | null = await fetchApi<User[]>(
        `/organizations/${organizationId}/users`,
        {
            cache: "no-store",
        },
    );

    const organization = await fetchApi<Organization>(
        `/organizations/${organizationId}`,
    );

    if (!users) {
        return <div>Error loading users</div>;
    }

    return (
        <>
            <BreadcrumbHeader
                pathSegments={[
                    {
                        title: organization?.name || organizationId,
                        href: `/${organizationId}`,
                    },
                    { title: "Members", href: null },
                ]}
            />
            <MembersList users={users} organizationId={organizationId} />
        </>
    );
}
