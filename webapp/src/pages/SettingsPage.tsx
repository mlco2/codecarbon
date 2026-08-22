import { useNavigate } from "react-router-dom";
import useSWR from "swr";

import { User } from "@/api/schemas";
import { fetcher } from "@/api/swr";
import { cn } from "@/helpers/utils";
import {
    AccountCircleIcon,
    ArrowBackIosIcon,
    LockIcon,
} from "@/components/icons/figma-icons";

const USER_PROFILE_URL = import.meta.env.VITE_OIDC_PROFILE_URL;

/*
 * The Settings page from Figma frame 77:762.
 *
 * The frame has no sidebar rail and carries its own "Go back" control, so this is
 * a standalone page rather than a child of DashboardLayout — it is routed under
 * AuthGuard only.
 *
 * Layout: a hugging sub-nav beside a bounded content column, both starting at the
 * same top edge (the design aligns "Go back" with the "Profile" title). Figma
 * positions everything absolutely; here the design's measurements map onto
 * container padding and gaps:
 *   sub-nav      rows 20px/10px padding, 4px radius, 4px gap; 24px icon then a
 *                10px-padded label. Its 163px width in the frame is exactly its
 *                hug-content width, so no width is set.
 *   content      the input row is 466 + 4 + 106 = 576px wide, which is `max-w-xl`
 *                to the pixel, so that bounds the column. The frame's rule is
 *                drawn 627px wide; it spans the column here instead.
 *   nav <-> body 35px in the frame -> gap-9
 *
 * Selected sub-nav row: #2b2b2b fill with a #BFFB4F label. Unselected rows are
 * white at 50% opacity, exactly as the design draws them.
 */

const NAV_ROW =
    "flex items-center gap-0 rounded-menu px-5 py-2.5 text-left outline-none " +
    "focus-visible:ring-2 focus-visible:ring-cc-lime";

/*
 * Interactive states for the sub-nav rows. The design draws unselected rows at
 * 50% opacity and gives no hover or pressed state, so these build on what it does
 * define: hover brings the row to full opacity over a #2b2b2b wash — the same
 * fill the selected row uses — and pressing settles on that fill outright.
 * Disabled rows stay flat.
 */
const NAV_ROW_INTERACTIVE =
    "cursor-pointer opacity-50 transition " +
    "hover:opacity-100 hover:bg-cc-darkest-gray/50 " +
    "active:bg-cc-darkest-gray active:opacity-100 " +
    "disabled:cursor-not-allowed disabled:opacity-50 " +
    "disabled:hover:bg-transparent motion-reduce:transition-none";

const NAV_LABEL = "type-display type-settings-nav whitespace-nowrap p-2.5";

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
                {/* Sub-nav — Figma 77:885 */}
                <nav
                    aria-label="Settings"
                    className="flex shrink-0 flex-col gap-1"
                >
                    <button
                        type="button"
                        onClick={() => navigate(-1)}
                        className={cn(NAV_ROW, NAV_ROW_INTERACTIVE)}
                    >
                        <ArrowBackIosIcon className="size-6 shrink-0 text-cc-white" />
                        <span className={cn(NAV_LABEL, "text-cc-white")}>
                            Go back
                        </span>
                    </button>

                    {/* Profile is the only panel the design defines, so it is the
                        page's content and this row is the selected one. */}
                    <span
                        aria-current="page"
                        className={cn(NAV_ROW, "bg-cc-darkest-gray")}
                    >
                        <AccountCircleIcon className="size-6 shrink-0 text-cc-lime" />
                        <span className={cn(NAV_LABEL, "text-cc-lime")}>
                            Profile
                        </span>
                    </span>

                    <button
                        type="button"
                        onClick={goToProvider}
                        disabled={!USER_PROFILE_URL}
                        className={cn(NAV_ROW, NAV_ROW_INTERACTIVE)}
                    >
                        <LockIcon className="size-6 shrink-0 text-cc-white" />
                        <span className={cn(NAV_LABEL, "text-cc-white")}>
                            Password
                        </span>
                    </button>
                </nav>

                {/* Content — Figma 77:951 / 218:15560 / 77:952 / 77:771 / 218:15559 */}
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
                            <label htmlFor="settings-email" className="sr-only">
                                Email address
                            </label>
                            <input
                                id="settings-email"
                                type="email"
                                readOnly
                                disabled
                                value={email ?? ""}
                                placeholder={isLoading ? "" : "Disabled"}
                                className="type-mono-regular type-field h-control min-w-0 flex-1 rounded-field bg-white/12 px-4 text-cc-text-input-gray placeholder:text-cc-text-input-gray disabled:cursor-not-allowed"
                            />
                            <button
                                type="button"
                                onClick={goToProvider}
                                disabled={!USER_PROFILE_URL}
                                className="type-mono-regular type-field shrink-0 cursor-pointer rounded-field bg-cc-lime px-6 py-2 text-cc-background outline-none transition hover:bg-cc-button-hover active:bg-cc-button-hover active:brightness-90 focus-visible:ring-2 focus-visible:ring-cc-white focus-visible:ring-offset-2 focus-visible:ring-offset-cc-background disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-cc-lime disabled:active:brightness-100 motion-reduce:transition-none"
                            >
                                Change
                            </button>
                        </div>
                    </section>
                </div>
            </div>
        </div>
    );
}
