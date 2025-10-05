import ErrorMessage from "@/components/error-message";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { User } from "@/types/user";
import { fetchApiServer } from "@/helpers/api-server";

async function getUser(): Promise<User | null> {
    // TODO: implement without fief
    const userId = null;
    if (!userId) {
        return null;
    }

    return await fetchApiServer<User>(`/users/${userId}`);
}

export default async function ProfilePage() {
    const user = await getUser();

    if (!user) {
        return <ErrorMessage />;
    }

    return (
        <div>
            <div className="px-4 space-y-6 md:px-6">
                <div className="space-y-1.5">
                    <div className="flex items-center space-x-4">
                        <div className="space-y-1.5">
                            <h1 className="text-2xl font-bold">{user?.name}</h1>
                            <p className="text-gray-500 dark:text-gray-400">
                                {user?.email}
                            </p>
                        </div>
                    </div>
                </div>
                <div className="space-y-6">
                    <div className="space-y-2">
                        <h2 className="text-lg font-semibold">
                            Personal Information
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <Label htmlFor="name">Name</Label>
                                <Input
                                    id="name"
                                    value={user?.name}
                                    placeholder="Enter your name"
                                    defaultValue="Catherine Grant"
                                />
                            </div>
                            <div>
                                <Label htmlFor="email">Email</Label>
                                <Input
                                    id="email"
                                    disabled
                                    value={user?.email}
                                    placeholder="Enter your email"
                                    type="email"
                                />
                            </div>
                        </div>
                    </div>
                    <div className="space-y-2">
                        <h2 className="text-lg font-semibold">
                            Change Password
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <Label htmlFor="current-password">
                                    Current Password
                                </Label>
                                <Input
                                    id="current-password"
                                    disabled
                                    placeholder="Enter your current password"
                                    type="password"
                                />
                            </div>
                            <div>
                                <Label htmlFor="new-password">
                                    New Password
                                </Label>
                                <Input
                                    id="new-password"
                                    disabled
                                    placeholder="Enter your new password"
                                    type="password"
                                />
                            </div>
                            <div>
                                <Label htmlFor="confirm-password">
                                    Confirm Password
                                </Label>
                                <Input
                                    id="confirm-password"
                                    disabled
                                    placeholder="Confirm your new password"
                                    type="password"
                                />
                            </div>
                        </div>
                    </div>
                </div>
                <div className="mt-8">
                    <Button type="submit" size="lg">
                        Save
                    </Button>
                </div>
            </div>
        </div>
    );
}
