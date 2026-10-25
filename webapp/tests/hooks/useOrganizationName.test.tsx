import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { SWRConfig } from "swr";

const fetcherMock = vi.hoisted(() => vi.fn());
vi.mock("@/api/swr", () => ({ fetcher: fetcherMock, swrConfig: {} }));

import { useOrganizationName } from "@/hooks/useOrganizationName";

function render(organizationId: string) {
    return renderHook(() => useOrganizationName(organizationId), {
        wrapper: ({ children }) => (
            <SWRConfig value={{ provider: () => new Map() }}>
                {children}
            </SWRConfig>
        ),
    });
}

beforeEach(() => {
    fetcherMock.mockReset();
    localStorage.clear();
});

describe("useOrganizationName", () => {
    it("shows the fetched name", async () => {
        fetcherMock.mockResolvedValue({ id: "o2", name: "Wecasa" });
        const { result } = render("o2");
        await waitFor(() => expect(result.current).toBe("Wecasa"));
        expect(fetcherMock).toHaveBeenCalledWith("/organizations/o2");
    });

    it("uses the cached name while fetching when it is this organization's", () => {
        fetcherMock.mockReturnValue(new Promise(() => {}));
        localStorage.setItem("organizationId", "o1");
        localStorage.setItem("organizationName", "Mozilla");
        expect(render("o1").result.current).toBe("Mozilla");
    });

    it("never shows another organization's cached name", () => {
        fetcherMock.mockReturnValue(new Promise(() => {}));
        localStorage.setItem("organizationId", "o1");
        localStorage.setItem("organizationName", "Mozilla");
        expect(render("o2").result.current).toBe("o2");
    });
});
