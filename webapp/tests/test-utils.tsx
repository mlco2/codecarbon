import { ReactElement } from "react";
import { render, RenderOptions } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

interface RouterRenderOptions extends Omit<RenderOptions, "wrapper"> {
    initialEntries?: string[];
}

export function renderWithRouter(
    ui: ReactElement,
    { initialEntries = ["/"], ...options }: RouterRenderOptions = {},
) {
    return render(ui, {
        ...options,
        wrapper: ({ children }) => (
            <MemoryRouter initialEntries={initialEntries}>
                {children}
            </MemoryRouter>
        ),
    });
}
