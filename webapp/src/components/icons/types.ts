/*
 * Single declaration of the contract for every icon in this directory.
 *
 * An icon takes nothing but a class: it draws with `currentColor` and at the
 * size its caller gives it, so state colour and dimensions belong to the
 * control around it rather than to the glyph.
 *
 * Named for where the set comes from: nearly all of these are exported verbatim
 * from the Code Carbon Figma file. A few were not in the Figma and were
 * designed apart from the rest, but in the same style, and they share this same
 * contract. Seeing `FigmaIconProps` in a module is the quiet signal that the
 * icon was added during the dashboard redesign.
 */
export type FigmaIconProps = {
    className?: string;
};
