import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const isMockModeMock = vi.hoisted(() => vi.fn(() => false));
const loginMockFn = vi.hoisted(() => vi.fn());
vi.mock("@/api/mock", () => ({
    isMockMode: isMockModeMock,
    loginMock: loginMockFn,
}));

const redirectToLoginMock = vi.hoisted(() => vi.fn());
vi.mock("@/api/auth", () => ({
    redirectToLogin: redirectToLoginMock,
    buildLoginUrl: () => "http://api.test/api/auth/login",
}));

import LandingPage from "@/pages/LandingPage";

beforeEach(() => {
    isMockModeMock.mockReset();
    loginMockFn.mockReset();
    redirectToLoginMock.mockReset();
});

describe("LandingPage", () => {
    it("renders the real-login button when not in mock mode", async () => {
        isMockModeMock.mockReturnValue(false);
        render(<LandingPage />);
        const button = screen.getByTestId("real-login");
        expect(button).toBeEnabled();
        await userEvent.click(button);
        expect(redirectToLoginMock).toHaveBeenCalledOnce();
    });

    it("does not render the real-login button in mock mode (mock-only UX)", () => {
        isMockModeMock.mockReturnValue(true);
        render(<LandingPage />);
        expect(screen.queryByTestId("real-login")).not.toBeInTheDocument();
    });

    it("renders the mock-mode button and dispatches loginMock on click", async () => {
        isMockModeMock.mockReturnValue(true);
        render(<LandingPage />);
        const button = screen.getByTestId("mock-login");
        await userEvent.click(button);
        expect(loginMockFn).toHaveBeenCalledOnce();
    });
});
