import { useNavigate } from "react-router-dom";
import useSWR from "swr";

import { User } from "@/api/schemas";
import { fetcher } from "@/api/swr";
import SettingsNavItem from "@/components/settings-nav-item";
import { FormField } from "@/components/ui/form-field";
import { PrimaryButton } from "@/components/ui/primary-button";
import { AccountCircleIcon } from "@/components/icons/account-circle-icon";
import { ArrowBackIosIcon } from "@/components/icons/arrow-back-ios-icon";
import { LockIcon } from "@/components/icons/lock-icon";

const USER_PROFILE_URL = import.meta.env.VITE_OIDC_PROFILE_URL;

/*
 * The Settings page: a hugging sub-nav beside a bounded content column, both
 * starting at the same top edge.
 *
 * The frame has no sidebar rail and carries its own "Go back" control, so this
 * is a standalone page routed under AuthGuard rather than a child of
 * DashboardLayout.
 */

export default function SettingsPage() {
    const navigate = useNavigate();

    // The signed-in user's real email, from the endpoint AuthGuard already uses.
    // Figma shows the field in its "Disabled" state with placeholder text; the
    // value here is the actual address rather than that placeholder.
    const { data: auth, isLoading } = useSWR<{ user?: User }>(
        "/auth/check",
        fetcher,
        { revalidateOnFocus: false },
    );
    const email = auth?.user?.email;

    /*
     * Email address and password are both owned by the OIDC provider — the API
     * exposes no endpoint for either, and the previous navigation's "Profile"
     * item already sent users there. So "Change" and "Password" hand off to it,
     * and are disabled when no provider URL is configured.
     */
    const goToProvider = () => {
        if (USER_PROFILE_URL) window.location.href = USER_PROFILE_URL;
    };

    return (
        <div className="min-h-dvh bg-cc-background">
            <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-5 pb-12 pt-6 sm:flex-row sm:gap-9 sm:px-6 sm:pt-16 lg:pt-48">
                {/* Sub-nav */}
                <nav
                    aria-label="Settings"
                    className="flex shrink-0 flex-col gap-1"
                >
                    <SettingsNavItem
                        icon={ArrowBackIosIcon}
                        label="Go back"
                        onClick={() => navigate(-1)}
                    />

                    {/* Profile is the only panel the design defines, so it is
                        the page's content and this row is the selected one. */}
                    <SettingsNavItem
                        icon={AccountCircleIcon}
                        label="Profile"
                        isCurrent
                    />

                    <SettingsNavItem
                        icon={LockIcon}
                        label="Password"
                        onClick={goToProvider}
                        disabled={!USER_PROFILE_URL}
                    />
                </nav>

                {/* Content */}
                <div className="min-w-0 flex-1">
                    <h1 className="type-display type-settings-title border-b border-cc-gray pb-3 text-cc-white lg:pb-4">
                        Profile
                    </h1>

                    <section className="flex max-w-xl flex-col gap-3 pt-6 lg:gap-4 lg:pt-8">
                        <h2 className="type-mono-medium type-settings-section text-cc-white">
                            Email
                        </h2>
                        <p className="type-mono-medium type-field text-cc-white">
                            Manage your email address to receive important
                            updates and notifications
                        </p>

                        <div className="flex items-end gap-1 pt-2">
                            <FormField
                                id="settings-email"
                                label="Email address"
                                hideLabel
                                type="email"
                                readOnly
                                disabled
                                value={email ?? ""}
                                placeholder={isLoading ? "" : "Disabled"}
                                containerClassName="min-w-0 flex-1"
                                className="bg-white/12 text-cc-text-input-gray"
                            />
                            <PrimaryButton
                                onClick={goToProvider}
                                disabled={!USER_PROFILE_URL}
                                className="shrink-0"
                            >
                                Change
                            </PrimaryButton>
                        </div>
                    </section>
                </div>
            </div>
        </div>
    );
}
