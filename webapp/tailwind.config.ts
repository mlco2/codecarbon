import type { Config } from "tailwindcss";

const config = {
    darkMode: ["class"],
    content: ["./index.html", "./src/**/*.{ts,tsx}"],
    prefix: "",
    theme: {
        container: {
            center: true,
            padding: "2rem",
            screens: {
                "2xl": "1400px",
            },
        },
        extend: {
            spacing: {
                /*
                 * Structural dimensions from the redesign, each defined once
                 * and only where it belongs.
                 *
                 * `rail` is the compact sidebar's own width. `gauge` is the
                 * consumed-energy ring's diameter (Figma 199.23, normalised —
                 * the ring's proportions live in the SVG viewBox, so the
                 * rendered size is free). `heading` is the gap between a
                 * section heading and its content (Figma 46px, which is off
                 * the default scale but consistent across both sections).
                 */
                rail: "101px",
                gauge: "200px",
                heading: "46px",
                /* Account menu panel width and row/field control height. */
                control: "46px",
            },
            boxShadow: {
                /* Figma 218:14541 — account menu panel. */
                menu: "0 4px 10px rgba(0, 0, 0, 0.25)",
                /* Figma 218:11927 — modal panel. */
                dialog: "0 4px 20px rgba(0, 0, 0, 0.25)",
            },
            fontFamily: {
                // IBM Plex Mono. `font-mono` is already applied on <body>.
                mono: ["var(--font-mono)"],
                // Disket Mono Bold — the design's display face, self-hosted
                // from public/fonts. See the note in globals.css.
                display: ["var(--font-display)"],
            },
            colors: {
                /*
                 * Figma variables from frame 218:7838, added additively. The
                 * existing shadcn tokens below are untouched: `--primary`
                 * already resolves to #BFFB4F and `--background` to #181818,
                 * so those two are reused rather than duplicated in markup.
                 */
                cc: {
                    background: "var(--cc-background)",
                    "page-background": "var(--cc-page-background)",
                    lime: "var(--cc-lime)",
                    white: "var(--cc-white)",
                    "dark-gray": "var(--cc-dark-gray)",
                    "darkest-gray": "var(--cc-darkest-gray)",
                    gray: "var(--cc-gray)",
                    "button-hover": "var(--cc-button-hover)",
                    "text-input-gray": "var(--cc-text-input-gray)",
                    "breadcrumb-gray": "var(--cc-breadcrumb-gray)",
                    rule: "var(--cc-rule)",
                    "gauge-track": "var(--cc-gauge-track)",
                    "gauge-label": "var(--cc-gauge-label)",
                },
                border: "hsl(var(--border))",
                input: "hsl(var(--input))",
                ring: "hsl(var(--ring))",
                background: "hsl(var(--background))",
                foreground: "hsl(var(--foreground))",
                primary: {
                    DEFAULT: "hsl(var(--primary))",
                    foreground: "hsl(var(--primary-foreground))",
                },
                secondary: {
                    DEFAULT: "hsl(var(--secondary))",
                    foreground: "hsl(var(--secondary-foreground))",
                },
                destructive: {
                    DEFAULT: "hsl(var(--destructive))",
                    foreground: "hsl(var(--destructive-foreground))",
                },
                muted: {
                    DEFAULT: "hsl(var(--muted))",
                    foreground: "hsl(var(--muted-foreground))",
                },
                accent: {
                    DEFAULT: "hsl(var(--accent))",
                    foreground: "hsl(var(--accent-foreground))",
                },
                popover: {
                    DEFAULT: "hsl(var(--popover))",
                    foreground: "hsl(var(--popover-foreground))",
                },
                card: {
                    DEFAULT: "hsl(var(--card))",
                    foreground: "hsl(var(--card-foreground))",
                },
            },
            borderRadius: {
                /* Design-specific radii from the Figma frame. */
                menu: "4px",
                field: "2px",
                lg: "var(--radius)",
                md: "calc(var(--radius) - 2px)",
                sm: "calc(var(--radius) - 4px)",
            },
            keyframes: {
                "accordion-down": {
                    from: { height: "0" },
                    to: { height: "var(--radix-accordion-content-height)" },
                },
                "accordion-up": {
                    from: { height: "var(--radix-accordion-content-height)" },
                    to: { height: "0" },
                },
            },
            animation: {
                "accordion-down": "accordion-down 0.2s ease-out",
                "accordion-up": "accordion-up 0.2s ease-out",
            },
        },
    },
    plugins: [require("tailwindcss-animate")],
} satisfies Config;

export default config;
