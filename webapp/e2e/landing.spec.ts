import { test, expect } from "@playwright/test";

test.describe("Landing page (mock mode)", () => {
    test("renders welcome heading and both sign-in buttons", async ({
        page,
    }) => {
        await page.goto("/");

        await expect(
            page.getByRole("heading", { name: /welcome to code carbon/i }),
        ).toBeVisible();

        await expect(
            page.getByRole("link", {
                name: /sign in or create an account/i,
            }),
        ).toBeVisible();

        await expect(page.getByTestId("mock-login")).toBeVisible();
    });

    test("clicking 'Login in mock mode' lands on the dashboard", async ({
        page,
    }) => {
        await page.goto("/");
        await page.getByTestId("mock-login").click();

        // After mock login we should land in the authenticated app shell.
        await expect(page).toHaveURL(/\/home/);
        // The dashboard layout pulls organizations from /organizations,
        // which the mock returns. We just assert we're past the auth wall.
        await expect(
            page.getByRole("heading", { name: /welcome to code carbon/i }),
        ).toHaveCount(0);
    });
});
