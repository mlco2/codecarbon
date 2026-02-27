import { useCallback, useState } from "react";

/**
 * Custom hook for managing modal open/close state
 * Reduces boilerplate for modal state management
 *
 * @param defaultOpen - Initial open state (default: false)
 * @returns Object with isOpen state and open/close/toggle functions
 */
export function useModal(defaultOpen = false) {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    const open = useCallback(() => setIsOpen(true), []);
    const close = useCallback(() => setIsOpen(false), []);
    const toggle = useCallback(() => setIsOpen((prev) => !prev), []);

    return { isOpen, open, close, toggle, setIsOpen };
}
