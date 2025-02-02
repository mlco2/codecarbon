import { User } from "@/types/user";
import MembersList from "./members-list";
import { fetchApi } from "@/utils/api";

export default async function MembersPage({
    params,
}: {
    params: Promise<{ organizationId: string }>;
}) {
    const { organizationId } = await params;

    const users: User[] | null = await fetchApi<User[]>(
        `/organizations/${organizationId}/users`,
    );

    if (!users) {
        return <div>Error loading users</div>;
    }

    return <MembersList users={users} organizationId={organizationId} />;
}
