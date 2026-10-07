import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RemoveMemberModal from "@/components/remove-member-modal";

beforeEach(() => {
    vi.restoreAllMocks();
});

function renderModal(overrides: Partial<{ onRemove: () => Promise<void> }>) {
    const onRemove = overrides.onRemove ?? vi.fn().mockResolvedValue(undefined);
    render(
        <RemoveMemberModal
            open={true}
            onOpenChange={() => {}}
            memberName="Alice"
            memberId="u1"
            organizationName="Acme"
            onRemove={onRemove}
        />,
    );
    return onRemove;
}

describe("RemoveMemberModal", () => {
    it("names the member and the organization being left", () => {
        renderModal({});
        expect(screen.getByText("Alice")).toBeInTheDocument();
        expect(screen.getByText(/Acme/)).toBeInTheDocument();
    });

    it("calls onRemove with the member id when confirmed", async () => {
        const onRemove = renderModal({});
        await userEvent.click(
            screen.getByRole("button", { name: /remove member/i }),
        );
        expect(onRemove).toHaveBeenCalledWith("u1");
    });

    it("does not call onRemove when cancelled", async () => {
        const onRemove = renderModal({});
        await userEvent.click(screen.getByRole("button", { name: /cancel/i }));
        expect(onRemove).not.toHaveBeenCalled();
    });
});
