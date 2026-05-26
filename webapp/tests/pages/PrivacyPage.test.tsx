import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import PrivacyPage from "@/pages/PrivacyPage";

describe("PrivacyPage", () => {
    it("renders the policy headline and core sections", () => {
        render(<PrivacyPage />);
        expect(
            screen.getByRole("heading", { name: /privacy policy/i }),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("heading", { name: /data collection/i }),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("heading", { name: /data retention/i }),
        ).toBeInTheDocument();
    });
});
