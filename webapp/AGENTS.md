# Webapp agent instructions

Scope: everything under `webapp/`. The repository root has its own `AGENTS.md`
covering the Python package and the API — this file adds to it, and wins where
the two disagree about webapp code.

## Working agreement

1. **Propose before editing.** Read the relevant code first, then say what will
   change and where, and stop for approval. Do not edit on the same turn as the
   proposal — the review gate is the point, so an unrequested implementation is
   the failure mode even when the change looks obvious.
2. **Follow the tests.** Check `tests/` for coverage of the feature being
   touched and update it in the same change. If nothing covers it but a similar
   component or page is tested, ask before adding new tests rather than
   inventing a convention.
3. **Sweep the docs.** After a change, check the `*.md` files for anything it
   invalidates and update them briefly — what is necessary, not a rewrite.
4. **Hand over the commit; never make it.** See [Commits](#commits) — this one
   has no exceptions.

## Commits

**Never commit. Never stage.** Not with `git commit`, not with `git add`, not as
a convenience at the end of a task — leave both to the user, every time.

Finish instead by giving the commit message as text: medium length, neither a
one-liner nor a changelog. Only what matters, not verbose — what changed, and
why it matters.

Then ask whether to fold anything already staged into the same message, rather
than assuming either way.

## Stack

React 19 + Vite + TypeScript, Tailwind v4, Radix primitives, SWR for fetching,
Zod for response schemas, `sonner` for toasts, `react-router-dom` v7. `pnpm` is
the package manager, Node 24 in CI. `@/` resolves to `src/`.

## Layout

-   `src/api/` — one module per resource, plus `client.ts` (fetch wrapper),
    `schemas.ts` (Zod types), `swr.ts` (hooks), `errors.ts`.
-   `src/components/` — kebab-case files. `src/components/ui/` holds the shared
    primitives, `src/components/icons/` the SVG icons.
-   `src/pages/` — PascalCase, one per route; `src/layouts/`, `src/hooks/`,
    `src/helpers/`, `src/utils/` as named.
-   `tests/` — Vitest + Testing Library, mirroring `src/`. `e2e/` — Playwright.

## Component conventions

There are two generations of UI primitives in `src/components/ui/`. The
redesign ones — `form-field.tsx`, `modal-header.tsx`, `primary-button.tsx`,
`secondary-button.tsx`, `icon-button.tsx`, `menu.tsx`, `tab-nav.tsx`,
`breadcrumb.tsx` — carry the current design. The older shadcn ones —
`input.tsx`, `label.tsx`, `button.tsx`, `card.tsx` — remain only because
pre-redesign screens still use them. **New work uses the redesign layer.**

Modals share one shell; copy it rather than restating it:

```tsx
<Dialog open={isOpen} onOpenChange={handleClose}>
    {/* The design's own close control lives in the header, so the shared
        corner button is omitted. */}
    <DialogContent
        hideClose
        className="max-w-[560px] gap-0 rounded-none border-2 border-black bg-cc-background p-0 shadow-dialog"
    >
        <ModalHeader title="Create thing" />
        <form className="flex flex-col gap-7 px-6 py-8 sm:px-10 sm:py-10" onSubmit={...}>
            <FormField id="thing-name" label="Name" placeholder="Name" required ... />
            <div className="flex pt-4">
                <PrimaryButton type="submit" disabled={isLoading || !name.trim()}>
                    Create thing
                </PrimaryButton>
            </div>
        </form>
    </DialogContent>
</Dialog>
```

`create-project-modal.tsx`, `create-experiment-modal.tsx` and
`create-organization-modal.tsx` are the reference implementations. Submission
goes through `toast.promise`; the submit button is disabled while pending and
while the required field is blank, instead of validating on click.

## Implementing a Figma design

The task supplies the frame link, and sometimes a note that the screen closely
resembles an existing one — verify that claim against the design before leaning
on it. Implement every state the design provides in one pass.

### The four things that matter most

1. **Responsive, not pixel-perfect.** Frames are 1440x1024 desktop only; there
   is no mobile design. Don't reproduce absolute coordinates or fixed sizes —
   one container gutter for horizontal placement, gaps for vertical rhythm,
   working down to ~320px. Make the mobile calls yourself, coherently.

2. **Ask when the design shows what the app doesn't have.** This is a UI
   redesign, not an architecture redesign. Data with no API field, menus whose
   contents are undrawn, controls with no defined action — stop and ask rather
   than inventing endpoints or features. Batch every question into one round
   before coding, recommendation first.

    Decide these yourself instead of asking: contradictory measurements for one
    edge (pick one, comment why), sizes that differ between two frames of the
    same component, and elements that are plainly a Figma component default
    rather than intent. Report what you decided afterwards.

3. **Extend the redesign; don't start a parallel style.** First find out where
   the redesign stands: read whatever screens and shared primitives already
   follow it. If nothing does, this is the first page and you are setting the
   vocabulary — build the recurring treatments as shared components from the
   start rather than inline, so the next page has something to inherit. If work
   already exists, take the page shell from it, reuse every primitive that fits,
   and extend one with a prop rather than forking it; add new shared components
   only where the design genuinely introduces something the existing set has no
   answer for. Either way, shared chrome — navigation, account menu — stays in
   its own components: never rebuild an in-page nav, even where an older frame
   draws one.

4. **Components, not class-string constants.** Never `const FOO = "flex
items-center …"` as a styling layer, and no helpers module of class strings.
   A repeated treatment is a component in `ui/`. Local constants are fine only
   when two elements inside one component share them.

### House style for design work

-   Tokens only: the design system's colour and type tokens, and the spacing and
    radius scales in the Tailwind config. No hardcoded hex or font sizes.
-   kebab-case filenames, PascalCase components; pages stay PascalCase.
-   Comments are sparse and concise, and explain reasoning only: why a value
    differs from the design, how an unspecified case was resolved. Never narrate
    the code or explain routine implementation. No long blocks, no Figma node
    ids. Wrap at 80 columns.
-   Respect `prefers-reduced-motion`; tie labels to inputs, keep focus-visible
    rings, set `aria-current` on the current item, give icon-only buttons
    `sr-only` text.
-   Verify with `tsc`, eslint, prettier, vitest and `vite build`, and update any
    test whose copy changed. You cannot see the app running — it needs the API —
    so state what is unverified rather than implying you checked it.

### Known traps — check only the ones the page actually hits

Ignore the rest; none of these are things to go hunting for.

-   **A `type-*` class not taking effect.** If a primitive from the underlying
    component library sets its own `text-*`, twMerge keeps both and the utility
    wins (a 24px title renders at 18px). There, and only there, name the size as
    a utility; everywhere else `type-*` remains the convention.
-   **Building a dialog:** ours are flex-centred and fade + rise in place
    (`cc-dialog-*`). Don't reintroduce transform centring or `slide-in-from-*`.
-   **Adding a dropdown to a padded trigger:** Radix anchors to the trigger's
    box, not its glyph — cancel the padding with `sideOffset`/`alignOffset`.
-   **Gating an SWR key on transient UI state** (a menu's `open`, say): the data
    vanishes when it flips and the UI visibly regroups. Latch the condition.
-   **A mutation that refetches while a form is open:** key reset effects on ids
    or fields so the refresh can't clobber in-progress edits.
-   **Rows in a list:** the row text lights as one item on hover, with the
    actions cell excluded so its small trigger reports its own hitbox, and
    padding on the link so the whole band is clickable. Follow whatever row the
    redesign already has.
-   **Forms:** a real `<form>` so Enter submits, the primary disabled until the
    required fields are filled, no closing on failure, transient state reset on
    open.
-   **A modal that duplicates an existing page:** prefer opening in place, and
    ask before deleting anything.

### When the work is done

Report (a) everything that differed from the design and every decision the
design didn't specify, grouped and concise, for the PR remarks, and (b) a
conventional-commit message, per [Commits](#commits).

## Styling

Design tokens live in `tailwind.config.ts` and `src/globals.css`: `cc-*` colors,
`h-control`, `rounded-field`, `shadow-dialog`, the `type-*` type classes, and
the `rail`/`gauge`/`heading` spacing. Use them — do not hardcode hex values or
one-off pixel sizes. Merge classes with `cn()` from `@/helpers/utils`.

## Comments

Components carry a block comment explaining _why_ the thing is shaped the way it
is, often citing the Figma frame it comes from. Match that density: explain the
decision, not the syntax.

## Commands

```bash
pnpm dev            # dev server on http://localhost:3000
pnpm test:run       # unit tests once (pnpm test watches)
pnpm test:e2e       # Playwright
pnpm lint           # eslint
pnpm format         # prettier --write (4-space indent, from .prettierrc)
npx tsc --noEmit    # typecheck
```
