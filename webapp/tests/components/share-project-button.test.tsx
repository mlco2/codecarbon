import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import ShareProjectButton from "@/components/share-project-button";

const originalFetch = globalThis.fetch;

beforeEach(() => {
    globalThis.fetch = vi.fn(async () => ({
        ok: true,
        status: 200,
        json: async () => ({ encrypted_id: "enc-123" }),
    })) as unknown as typeof fetch;
});

afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
});

describe("ShareProjectButton", () => {
    it("renders nothing for private projects", () => {
        const { container } = render(
            <ShareProjectButton projectId="p1" isPublic={false} />,
        );
        expect(container.textContent).toBe("");
    });

    it("renders the share trigger for public projects", () => {
        render(<ShareProjectButton projectId="p1" isPublic={true} />);
        expect(
            screen.getByRole("button", { name: /share project/i }),
        ).toBeInTheDocument();
    });
});
