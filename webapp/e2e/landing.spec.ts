import { test, expect } from "@playwright/test";

test.describe("Landing page (mock mode)", () => {
    test("renders welcome heading and the mock-only login button", async ({
        page,
    }) => {
        await page.goto("/");

        await expect(
            page.getByRole("heading", { name: /welcome to code carbon/i }),
        ).toBeVisible();

        // In mock mode the real-login button is hidden — there is no real
        // OAuth backend in this build.
        await expect(page.getByTestId("real-login")).toHaveCount(0);
        await expect(page.getByTestId("mock-login")).toBeVisible();
    });

    test("clicking 'Mock Login' lands on the dashboard", async ({ page }) => {
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
