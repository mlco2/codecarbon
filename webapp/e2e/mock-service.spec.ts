import { test, expect, Page } from "@playwright/test";

const ORG_ID = "mock-org-1";
const PROJECT_ID = "mock-project-1";

async function logIn(page: Page) {
    await page.goto("/");
    await page.getByTestId("mock-login").click();
    // The mock login bounces to /home, which then redirects to /<org-id>
    // as soon as the mock organizations call resolves. Wait for either.
    await page.waitForURL(/\/(home|mock-org-1)/);
}

function collectConsoleErrors(page: Page): string[] {
    const errors: string[] = [];
    page.on("console", (msg) => {
        if (msg.type() === "error") errors.push(msg.text());
    });
    page.on("pageerror", (err) => errors.push(err.message));
    return errors;
}

test.describe("Mock service end-to-end", () => {
    test("HomePage redirects to the mock org dashboard", async ({ page }) => {
        const errors = collectConsoleErrors(page);
        await logIn(page);

        // HomePage reads /organizations, picks the first, and navigates.
        await expect(page).toHaveURL(new RegExp(`/${ORG_ID}$`));
        expect(errors).toEqual([]);
    });

    test("Projects list shows both mock projects", async ({ page }) => {
        const errors = collectConsoleErrors(page);
        await logIn(page);
        await page.goto(`/${ORG_ID}/projects`);

        await expect(
            page.getByRole("heading", { name: /^projects$/i }),
        ).toBeVisible();
        // Each row is a link to the project, beside its "Actions for …" menu.
        await expect(
            page.getByRole("link", {
                name: "ML Training Pipeline",
                exact: true,
            }),
        ).toBeVisible();
        await expect(
            page.getByRole("link", { name: "Inference Service", exact: true }),
        ).toBeVisible();
        expect(errors).toEqual([]);
    });

    test("Project dashboard loads experiments, charts, and metrics", async ({
        page,
    }) => {
        const errors = collectConsoleErrors(page);
        await logIn(page);
        await page.goto(`/${ORG_ID}/projects/${PROJECT_ID}`);

        // The page title shows the project name — proves getOneProject
        // parsed the snake_case wire shape into the camelCase app shape.
        await expect(
            page.getByRole("heading", {
                level: 1,
                name: "ML Training Pipeline",
            }),
        ).toBeVisible();

        // Chart card titles render (skeleton would not include them).
        await expect(
            page.getByRole("heading", { name: "Project experiment runs" }),
        ).toBeVisible();
        await expect(
            page.getByRole("heading", { name: "Emissions by run" }),
        ).toBeVisible();

        // Experiments live in a Radix Select portal — open it to assert
        // the dropdown is populated from /projects/:id/experiments.
        await page.getByTestId("experiment-select").click();
        await expect(
            page.getByRole("option", { name: "Baseline run" }),
        ).toBeVisible();
        await expect(
            page.getByRole("option", { name: "Optimized model" }),
        ).toBeVisible();

        // Pick one — that fires runs/sums and the scatter chart hydrates.
        await page.getByRole("option", { name: "Baseline run" }).click();
        await expect(page.getByTestId("experiment-details")).toBeVisible();

        // Neither chart should be left on its "No data available" fallback —
        // that would mean the mock fetch interceptor missed a request.
        await expect(page.getByText(/no data available/i)).toHaveCount(0);

        expect(errors).toEqual([]);
    });

    test("Project settings modal shows the API tokens table", async ({
        page,
    }) => {
        const errors = collectConsoleErrors(page);
        await logIn(page);
        await page.goto(`/${ORG_ID}/projects/${PROJECT_ID}`);

        // Settings moved from their own page into a modal on the dashboard.
        await page.getByRole("button", { name: "Project settings" }).click();
        await page
            .getByRole("dialog", { name: "Project settings" })
            .getByRole("tab", { name: "API Tokens" })
            .click();

        // From MOCK.token.byProjectId:
        await expect(page.getByText("Local dev token")).toBeVisible();
        expect(errors).toEqual([]);
    });

    test("Org dashboard renders without ErrorMessage (single-org fetch works)", async ({
        page,
    }) => {
        const errors = collectConsoleErrors(page);
        await logIn(page);
        await page.goto(`/${ORG_ID}`);

        // OrgDashboardPage hits /organizations/<id> and /organizations/<id>/sums.
        // If either is missing from the mock, the page renders <ErrorMessage />.
        await expect(page.getByText(/an error occurred/i)).toHaveCount(0);

        // The gauges are labelled with their value and unit.
        await expect(
            page.getByRole("img", { name: /kg eq CO2$/ }),
        ).toBeVisible();
        expect(errors).toEqual([]);
    });

    test("Members page lists organization users", async ({ page }) => {
        const errors = collectConsoleErrors(page);
        await logIn(page);
        await page.goto(`/${ORG_ID}/members`);

        // MembersPage fetches /organizations/<id>/users — must not be the
        // ErrorMessage fallback.
        await expect(page.getByText(/an error occurred/i)).toHaveCount(0);

        await expect(
            page.getByText("Mock Admin", { exact: true }),
        ).toBeVisible();
        await expect(
            page.getByText("Mock Member", { exact: true }),
        ).toBeVisible();
        // The mock user administers this organization, so the per-member
        // actions are offered: /auth/check identifies them by `sub`.
        await expect(
            page.getByRole("button", { name: "Actions for Mock Member" }),
        ).toBeVisible();
        expect(errors).toEqual([]);
    });
});
