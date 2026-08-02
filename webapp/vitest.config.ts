/// <reference types="vitest" />
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: { "@": path.resolve(__dirname, "./src") },
    },
    test: {
        environment: "jsdom",
        globals: true,
        setupFiles: ["./tests/setup.ts"],
        css: false,
        env: {
            VITE_API_URL: "http://api.test/api",
            VITE_BASE_URL: "http://app.test",
            VITE_USE_MOCK_DATA: "false",
        },
        include: ["tests/**/*.{test,spec}.{ts,tsx}"],
        exclude: ["node_modules", "dist", "e2e/**"],
    },
});
