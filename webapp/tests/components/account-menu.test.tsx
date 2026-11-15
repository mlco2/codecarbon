import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const redirectToAccountMock = vi.hoisted(() => vi.fn());
const redirectToLogoutMock = vi.hoisted(() => vi.fn());
vi.mock("@/api/auth", () => ({
    redirectToAccount: redirectToAccountMock,
    redirectToLogout: redirectToLogoutMock,
}));

import AccountMenu from "@/components/account-menu";
import { renderWithRouter } from "../test-utils";

function renderMenu() {
    renderWithRouter(
        <AccountMenu>
            <button type="button">Account</button>
        </AccountMenu>,
    );
}

beforeEach(() => {
    redirectToAccountMock.mockReset();
    redirectToLogoutMock.mockReset();
});

describe("AccountMenu", () => {
    it("offers only the account actions once opened", async () => {
        renderMenu();
        await userEvent.click(screen.getByRole("button", { name: "Account" }));

        expect(
            await screen.findByRole("menuitem", { name: "Settings" }),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("menuitem", { name: "Log out" }),
        ).toBeInTheDocument();
        expect(screen.getAllByRole("menuitem")).toHaveLength(2);
    });

    it("leaves for the provider's account console from its own row", async () => {
        renderMenu();
        await userEvent.click(screen.getByRole("button", { name: "Account" }));
        await userEvent.click(
            await screen.findByRole("menuitem", { name: "Settings" }),
        );
        await waitFor(() => expect(redirectToAccountMock).toHaveBeenCalled());
    });

    it("logs out through the API from its own row", async () => {
        renderMenu();
        await userEvent.click(screen.getByRole("button", { name: "Account" }));
        await userEvent.click(
            await screen.findByRole("menuitem", { name: "Log out" }),
        );
        await waitFor(() => expect(redirectToLogoutMock).toHaveBeenCalled());
    });
});
