import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

/*
 * jsdom implements neither of these, and Radix reaches for both: `useSize`
 * observes a control's box (the switch does), and its popper measures scroll
 * geometry. Stubbed here rather than in each test, so a component that happens
 * to use one does not fail for a reason unrelated to what is being tested.
 */
if (!("ResizeObserver" in globalThis)) {
    globalThis.ResizeObserver = class {
        observe() {}
        unobserve() {}
        disconnect() {}
    } as unknown as typeof ResizeObserver;
}

if (!Element.prototype.scrollIntoView) {
    Element.prototype.scrollIntoView = () => {};
}

afterEach(() => {
    cleanup();
});
