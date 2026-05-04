import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

const isMockModeMock = vi.hoisted(() => vi.fn(() => false));
const loginMockFn = vi.hoisted(() => vi.fn());
vi.mock("@/api/mock", () => ({
    isMockMode: isMockModeMock,
    loginMock: loginMockFn,
}));

vi.mock("@/api/auth", () => ({
    buildLoginUrl: () => "http://api.test/api/auth/login?redirect=...",
    redirectToLogin: vi.fn(),
}));

import LandingPage from "./LandingPage";

beforeEach(() => {
    isMockModeMock.mockReset();
    loginMockFn.mockReset();
});

describe("LandingPage", () => {
    it("renders the main sign-in CTA", () => {
        isMockModeMock.mockReturnValue(false);
        render(<LandingPage />);
        const link = screen.getByRole("link", {
            name: /sign in or create an account/i,
        });
        expect(link).toHaveAttribute(
            "href",
            "http://api.test/api/auth/login?redirect=...",
        );
    });

    it("hides the mock-mode button when VITE_USE_MOCK_DATA is off", () => {
        isMockModeMock.mockReturnValue(false);
        render(<LandingPage />);
        expect(screen.queryByTestId("mock-login")).not.toBeInTheDocument();
    });

    it("shows the mock-mode button when VITE_USE_MOCK_DATA is on", () => {
        isMockModeMock.mockReturnValue(true);
        render(<LandingPage />);
        const button = screen.getByTestId("mock-login");
        expect(button).toBeInTheDocument();
        button.click();
        expect(loginMockFn).toHaveBeenCalledOnce();
    });
});
