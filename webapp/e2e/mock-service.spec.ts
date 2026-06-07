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
        await expect(page.getByText("ML Training Pipeline")).toBeVisible();
        await expect(page.getByText("Inference Service")).toBeVisible();
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
                name: /^project ml training pipeline$/i,
            }),
        ).toBeVisible();

        // Chart card titles render (skeleton would not include them).
        await expect(page.getByText(/project experiment runs/i)).toBeVisible();
        await expect(
            page.getByText(/scatter chart - emissions by run id/i),
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

    test("Project settings page shows the API tokens table", async ({
        page,
    }) => {
        const errors = collectConsoleErrors(page);
        await logIn(page);
        await page.goto(`/${ORG_ID}/projects/${PROJECT_ID}/settings`);

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

        // The radial cards contain unit labels — at least one should be visible.
        await expect(page.getByText("kg eq CO2").first()).toBeVisible();
        expect(errors).toEqual([]);
    });

    test("Members page lists organization users", async ({ page }) => {
        const errors = collectConsoleErrors(page);
        await logIn(page);
        await page.goto(`/${ORG_ID}/members`);

        // MembersPage fetches /organizations/<id>/users — must not be the
        // ErrorMessage fallback.
        await expect(page.getByText(/an error occurred/i)).toHaveCount(0);

        await expect(page.getByText("Mock Admin")).toBeVisible();
        await expect(page.getByText("Mock Member")).toBeVisible();
        expect(errors).toEqual([]);
    });
});
