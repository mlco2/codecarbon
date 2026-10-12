import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const copyMock = vi.hoisted(() => vi.fn(() => true));
vi.mock("copy-to-clipboard", () => ({
    default: copyMock,
}));

import ShareProjectButton from "@/components/share-project-button";

beforeEach(() => {
    copyMock.mockReset();
    copyMock.mockReturnValue(true);
});

afterEach(() => {
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

    it("uses the public project id in the sharing URL", async () => {
        render(<ShareProjectButton projectId="p1" isPublic={true} />);

        await userEvent.click(
            screen.getByRole("button", { name: /share project/i }),
        );

        const input = await screen.findByDisplayValue(
            /\/public\/projects\/p1$/,
        );
        expect(input).toBeInTheDocument();
    });
});
