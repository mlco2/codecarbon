import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { ApiError, ValidationError, handleError } from "./errors";
import { ZodError } from "zod";

const toastError = vi.hoisted(() => vi.fn());
vi.mock("sonner", () => ({
    toast: { error: toastError },
}));

const redirectMock = vi.hoisted(() => vi.fn());
vi.mock("./auth", () => ({
    redirectToLogin: redirectMock,
    buildLoginUrl: () => "http://api.test/api/auth/login?redirect=...",
}));

beforeEach(() => {
    toastError.mockReset();
    redirectMock.mockReset();
});

afterEach(() => {
    vi.restoreAllMocks();
});

describe("handleError", () => {
    it("redirects to login on 401 ApiError without showing toast", () => {
        handleError(new ApiError("nope", 401, "/projects"));
        expect(redirectMock).toHaveBeenCalledOnce();
        expect(toastError).not.toHaveBeenCalled();
    });

    it("toasts message on non-401 ApiError", () => {
        handleError(new ApiError("server boom", 500, "/projects"));
        expect(toastError).toHaveBeenCalledWith("server boom");
        expect(redirectMock).not.toHaveBeenCalled();
    });

    it("toasts a generic message on ValidationError", () => {
        const zodErr = new ZodError([]);
        handleError(new ValidationError("invalid", zodErr, "/projects"));
        expect(toastError).toHaveBeenCalledWith(
            "Received unexpected data from the server",
        );
    });

    it("toasts plain Error messages", () => {
        handleError(new Error("network down"));
        expect(toastError).toHaveBeenCalledWith("network down");
    });

    it("toasts a fallback message for unknown values", () => {
        handleError("not an error object");
        expect(toastError).toHaveBeenCalledWith("An unexpected error occurred");
    });
});
