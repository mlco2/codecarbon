import { defineConfig, devices } from "@playwright/test";

const PORT = 4173;

export default defineConfig({
    testDir: "./e2e",
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    reporter: process.env.CI ? "github" : "list",
    use: {
        baseURL: `http://localhost:${PORT}`,
        trace: "retain-on-failure",
    },
    projects: [
        {
            name: "chromium",
            use: { ...devices["Desktop Chrome"] },
        },
    ],
    webServer: {
        // Build with mock mode baked in, then preview the static bundle.
        // No backend, no auth — fully autonomous.
        command: `VITE_USE_MOCK_DATA=true VITE_API_URL=http://api.mock/api VITE_BASE_URL=http://localhost:${PORT} pnpm build && pnpm preview --port ${PORT} --strictPort`,
        url: `http://localhost:${PORT}`,
        reuseExistingServer: !process.env.CI,
        timeout: 180_000,
    },
});
