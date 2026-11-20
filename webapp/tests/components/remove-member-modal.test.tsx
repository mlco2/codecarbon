import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RemoveMemberModal from "@/components/remove-member-modal";

function renderModal(
    overrides: Partial<{ isRemoving: boolean; isOpen: boolean }> = {},
) {
    const onConfirm = vi.fn();
    const onClose = vi.fn();
    render(
        <RemoveMemberModal
            isOpen={overrides.isOpen ?? true}
            onClose={onClose}
            onConfirm={onConfirm}
            memberName="Alice"
            organizationName="Acme"
            isRemoving={overrides.isRemoving ?? false}
        />,
    );
    return { onConfirm, onClose };
}

describe("RemoveMemberModal", () => {
    it("names the member and the organization being left", () => {
        renderModal();
        expect(
            screen.getByText(/Remove Alice from Acme\?/),
        ).toBeInTheDocument();
    });

    it("renders nothing while closed", () => {
        renderModal({ isOpen: false });
        expect(screen.queryByText(/Remove Alice/)).not.toBeInTheDocument();
    });

    it("calls onConfirm when confirmed", async () => {
        const { onConfirm } = renderModal();
        await userEvent.click(
            screen.getByRole("button", { name: /remove member/i }),
        );
        expect(onConfirm).toHaveBeenCalledTimes(1);
    });

    it("does not confirm when cancelled", async () => {
        const { onConfirm, onClose } = renderModal();
        await userEvent.click(screen.getByRole("button", { name: /cancel/i }));
        expect(onClose).toHaveBeenCalledTimes(1);
        expect(onConfirm).not.toHaveBeenCalled();
    });

    it("disables both buttons while the removal is in flight", () => {
        renderModal({ isRemoving: true });
        expect(
            screen.getByRole("button", { name: /removing/i }),
        ).toBeDisabled();
        expect(screen.getByRole("button", { name: /cancel/i })).toBeDisabled();
    });
});
