import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const encryptProjectIdMock = vi.hoisted(() => vi.fn());
vi.mock("@/utils/crypto", () => ({
    encryptProjectId: encryptProjectIdMock,
}));

const copyMock = vi.hoisted(() => vi.fn(() => true));
vi.mock("copy-to-clipboard", () => ({
    default: copyMock,
}));

import ShareProjectButton from "@/components/share-project-button";

beforeEach(() => {
    encryptProjectIdMock.mockReset();
    encryptProjectIdMock.mockResolvedValue("enc-token-xyz");
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
        expect(encryptProjectIdMock).not.toHaveBeenCalled();
    });

    it("renders the share trigger for public projects", () => {
        render(<ShareProjectButton projectId="p1" isPublic={true} />);
        expect(
            screen.getByRole("button", { name: /share project/i }),
        ).toBeInTheDocument();
    });

    it("computes the encrypted id client-side when the popover opens", async () => {
        render(<ShareProjectButton projectId="p1" isPublic={true} />);

        await userEvent.click(
            screen.getByRole("button", { name: /share project/i }),
        );

        await waitFor(() =>
            expect(encryptProjectIdMock).toHaveBeenCalledWith("p1"),
        );

        // The encrypted token shows up in the share-link input.
        const input = await screen.findByDisplayValue(
            /\/public\/projects\/enc-token-xyz$/,
        );
        expect(input).toBeInTheDocument();
    });

    it("does not call the encryptor before the popover is opened", () => {
        render(<ShareProjectButton projectId="p1" isPublic={true} />);
        expect(encryptProjectIdMock).not.toHaveBeenCalled();
    });
});
