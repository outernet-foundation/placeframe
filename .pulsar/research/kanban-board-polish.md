# Kanban Board Visual Polish: Linear-Style Refinements

Research conducted 2026-03-02. Context: the Placeframe board (`apps/sveltekit/board/`) is functionally complete and already looks good — this research identifies the specific CSS refinements that separate "good first try" from "feels professionally designed."

## The question

What specific CSS/visual refinements — spacing, typography, shadows, borders, transitions, micro-interactions — distinguish a polished minimal kanban board (Linear-style) from a functional one? What patterns does Linear use that we could adopt within pure Tailwind v4 on a dark theme?

**Scope:** Primarily CSS polish; small structural tweaks only if high-impact. No component libraries, no light mode, no major layout changes. Everything cherry-pickable.

## Current state audit

The board already gets the fundamentals right:
- OKLCH-based color system with semantic naming (surface/text/border/status/epic)
- Clean three-tier text hierarchy (primary/secondary/muted)
- Two-tier border hierarchy (default/subtle) used as resting vs. interactive states
- Card hover pattern (border + background shift) is well-executed

### Issues found

| # | Issue | Severity |
|---|-------|----------|
| 1 | **No focus-visible states** on Card, epic buttons, close button, drop zone — keyboard users can't see what's focused | Accessibility |
| 2 | **Inconsistent transitions** — Card and drop zone have `transition-colors`, but epic buttons, close button, resize handle, and inputs snap instantly | Polish |
| 3 | **No hover on inputs** — SearchBar and epic select have focus states but no hover feedback | Polish |
| 4 | **Undefined `accent-500`** — resize handle uses `bg-accent-500/50` but no `--color-accent-*` exists in `@theme` | Bug |
| 5 | **Dead CSS custom properties** — `--color-epic-*` variables in `app.css` are never referenced (all epic coloring goes through TypeScript `epicColor()` + inline styles); `--color-surface-600` is also unused | Cleanup |
| 6 | **No active/pressed states** on any interactive element | Polish |
| 7 | **Native `<select>` dropdown** doesn't match dark theme | Visual |
| 8 | **Card `py-3.5`** (14px) breaks the 4px/8px spacing rhythm | Consistency |

## Findings: what makes Linear feel "Linear"

### 1. Borders over shadows

Linear's dark UI uses **borders and surface-lightness steps** as the primary depth mechanism, not drop shadows. Shadows are reserved for truly floating elements (modals, dropdowns). This is the single most important architectural choice.

The board already follows this pattern. The refinement opportunity is in *how* borders are rendered.

**`ring` instead of `border`:** Tailwind's `ring-1` renders via `box-shadow` — it doesn't affect layout, composes with actual shadows, and can transition smoothly via `transition-shadow`. Linear-style apps typically use `ring-1 ring-white/[0.06]` for card edges rather than `border border-border-subtle`.

| Technique | Pros | Cons |
|-----------|------|------|
| `border border-border-subtle` (current) | Explicit, familiar | Affects layout, can't compose with shadows |
| `ring-1 ring-white/[0.06]` | No layout shift, composes with shadow, adapts to any surface | Requires `transition-shadow` instead of `transition-colors` |
| `border border-white/[0.06]` | Keeps current structure, gains adaptability | Still affects layout |

**Recommendation:** The switch to `ring` is the "more correct" approach for cards, but the current `border` approach works fine. The real win is switching to **semi-transparent white borders** (`white/[0.06]` resting, `white/[0.12]` hover) which automatically adapt to any surface level.

### 2. Card hover lift

The single highest-impact micro-interaction for a polished feel. Linear-style cards lift slightly on hover:

```
translateY(-2px)  +  border/ring brightens  +  subtle shadow fades in
```

The shadow should be animated via the pseudo-element opacity trick (animate `opacity` on a `::after` with a pre-rendered shadow) rather than animating `box-shadow` directly, since `opacity` is GPU-composited and `box-shadow` triggers paint. However, in Tailwind without custom CSS, a simple `hover:shadow-md` with `transition-shadow` is acceptable for the small shadow sizes involved.

**Concrete Tailwind classes for a card:**
```
rounded-lg bg-surface-800 ring-1 ring-white/[0.06]
transition-all duration-200 ease-out
hover:ring-white/[0.12] hover:-translate-y-0.5 hover:bg-surface-700
```

The `-translate-y-0.5` (2px) is subtle enough for kanban cards. Linear.style uses `-translate-y-1` (4px) but their cards are larger.

### 3. Asymmetric transition timing

Premium UIs make hover-enter faster than hover-exit. The card responds instantly to your cursor (snappy) but settles back lazily (smooth). This creates a "physical object" feeling.

CSS supports this natively — the resting-state `transition` is the exit timing, and the `:hover` transition is the enter timing:

```css
.card {
  transition: all 250ms ease;           /* slow exit */
}
.card:hover {
  transition: all 120ms ease-out;       /* fast enter */
}
```

In Tailwind, this requires either a custom utility or a small CSS rule in `app.css`. The default `transition-all duration-200` applies symmetrically, which is fine but not premium.

### 4. Typography tightening

Two details that Linear gets right and most apps miss:

**Negative letter-spacing on headings.** As text gets larger, letter-spacing should get tighter. The page title ("Placeframe Board") at `text-lg` should have `tracking-tight` (-0.025em). Column headers at `text-sm font-semibold` are fine without adjustment.

**Font weight floor of 400.** On dark backgrounds, font weights below Regular (400) "disappear." The board doesn't use light weights, so this is already correct. The `font-medium` (500) on card IDs and epic chips is good practice.

**Letter-spacing reference:**

| Size | Tracking | Tailwind |
|------|----------|----------|
| >= 20px | -0.025em | `tracking-tight` |
| 16-18px | -0.011em | `tracking-[-0.011em]` or leave default |
| 14px | 0 | default |
| 12px | +0.0025em | `tracking-wide` is too much; leave default |

### 5. Spacing rhythm

The board mostly follows the 8px grid (Tailwind's scale is 4px-based, so `p-2` = 8px, `p-4` = 16px). One exception: card padding is `py-3.5` (14px), which breaks the rhythm. Changing to `py-3` (12px) tightens cards slightly (more Linear-like density) while staying on-grid.

**Column gap:** Currently `gap-4` (16px) between columns with `gap-2` (8px) between cards. Linear uses generous column spacing — bumping to `gap-5` (20px) or `gap-6` (24px) between columns would give more breathing room and make the status headers feel more distinct.

**Card gap:** The current `gap-2` (8px) is tight. `gap-2.5` (10px) or `gap-3` (12px) would be more spacious. Linear defaults to moderate density.

### 6. Focus-visible states

This is both an accessibility fix and a polish signal. Professionally designed apps have beautiful, themed focus rings.

```
focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-900
```

The `ring-offset` creates a gap between the element and the ring, which is the detail that makes focus rings look intentional rather than bolted-on. The offset color should match the background surface.

### 7. Transition consistency

Every element with a hover or focus state change should have a matching transition. Current gaps:

| Element | Has hover/focus? | Has transition? | Fix |
|---------|-----------------|-----------------|-----|
| Card | Yes | `transition-colors` | Change to `transition-all` (for transform lift) |
| Column drop zone | Yes (drag) | `transition-colors` | Fine |
| Epic section buttons | `hover:bg-surface-700` | **No** | Add `transition-colors` |
| Close button | `hover:bg-surface-700` | **No** | Add `transition-colors` |
| Resize handle | `hover:bg-accent-500/50` | **No** | Add `transition-colors` |
| SearchBar input | `focus:border-...` | **No** | Add `transition-colors` |
| Epic filter select | `focus:border-...` | **No** | Add `transition-colors` |

### 8. Active/pressed states

When you click a card or button, there should be a brief "push" feedback. The simplest approach:

```
active:scale-[0.98] active:duration-75
```

Or for background-based elements:
```
active:bg-surface-600
```

The short `duration-75` on active makes the press feel instant while the release animates at the normal duration.

### 9. Drop zone feedback

The current drag-over state changes border and background color. More polished approaches:

- **Dashed border** on the active drop zone: `border-dashed` signals "drop here" universally
- **Inset shadow** for a recessed appearance: `inset-shadow-sm inset-shadow-black/20`
- **Subtle pulse** on the drop zone border (requires `@keyframes`, probably not worth it)

### 10. Detail panel backdrop

The current backdrop is `bg-black/50`. Linear-style panels use a frosted glass effect:

```
bg-black/40 backdrop-blur-sm
```

The blur creates depth separation between the panel and the board without a harsh dark overlay. `backdrop-blur-sm` (4px) is subtle enough to not feel heavy.

### 11. Column header refinement

The status dot + label + count is clean. One refinement: the status dot could be slightly larger (`h-3 w-3` instead of `h-2.5 w-2.5`) and the count could be wrapped in a subtle pill shape for visual consistency with epic chips:

```
<span class="rounded-full bg-surface-700 px-1.5 py-0.5 text-xs text-text-muted">4</span>
```

This is a minor enhancement — the current plain text count is fine.

## Priority ranking

Ordered by impact-to-effort ratio. Each is independently cherry-pickable.

| # | Change | Impact | Effort | Category |
|---|--------|--------|--------|----------|
| 1 | Add `transition-colors` to all interactive elements missing it | High | Trivial | Consistency |
| 2 | Add `focus-visible` ring to Card, epic buttons, close button | High | Low | Accessibility |
| 3 | Card hover lift: `-translate-y-0.5` + `transition-all` | High | Low | Micro-interaction |
| 4 | Add `hover:border-border-default` to SearchBar and select | Medium | Trivial | Consistency |
| 5 | Increase column gap from `gap-4` to `gap-5` or `gap-6` | Medium | Trivial | Spacing |
| 6 | Add `tracking-tight` to page title | Medium | Trivial | Typography |
| 7 | Backdrop blur on detail panel: `backdrop-blur-sm` | Medium | Trivial | Depth |
| 8 | Fix undefined `accent-500` on resize handle | Medium | Trivial | Bug fix |
| 9 | Remove dead `--color-epic-*` and `--color-surface-600` CSS vars | Low | Trivial | Cleanup |
| 10 | Active/pressed state on cards: `active:scale-[0.98]` | Medium | Low | Micro-interaction |
| 11 | Card padding rhythm: `py-3.5` → `py-3` | Low | Trivial | Spacing |
| 12 | Card gap increase: `gap-2` → `gap-2.5` | Low | Trivial | Spacing |
| 13 | Semi-transparent borders: `border-white/[0.06]` | Low | Medium | Refinement |

## Techniques not recommended

- **Glassmorphism / heavy backdrop-blur on cards**: Looks impressive in demos but causes performance issues with many cards and doesn't match Linear's restrained aesthetic.
- **Colored shadows / glow effects**: Feels "gaming UI" rather than "productivity tool."
- **Switching to `ring` from `border` on cards**: Architecturally cleaner but would change every component for marginal visual difference. Not worth it unless doing a broader refactor.
- **Custom easing curves**: The default Tailwind `ease-out` and `ease-in-out` are good enough. Custom cubic-bezier curves add complexity for imperceptible difference at these short durations.
- **Asymmetric transition timing via CSS**: Requires custom CSS rules that break the "pure Tailwind" pattern. The symmetric `duration-200` is fine.

## Sources

- [How We Redesigned the Linear UI (Part II) — Linear Blog](https://linear.app/now/how-we-redesigned-the-linear-ui)
- [Linear.style — Community Design System Reference](https://linear.style/)
- [Linear — Radix Primitives Case Study](https://www.radix-ui.com/primitives/case-studies/linear)
- [Linear Design: The SaaS Design Trend — LogRocket](https://blog.logrocket.com/ux-design/linear-design/)
- [Designing Beautiful Shadows in CSS — Josh W. Comeau](https://www.joshwcomeau.com/css/designing-shadows/)
- [An Interactive Guide to CSS Transitions — Josh W. Comeau](https://www.joshwcomeau.com/animation/css-transitions/)
- [How to Animate Box-Shadow — Tobias Ahlin](https://tobiasahlin.com/blog/how-to-animate-box-shadow/)
- [Better Dynamic Themes in Tailwind with OKLCH — Evil Martians](https://evilmartians.com/chronicles/better-dynamic-themes-in-tailwind-with-oklch-color-magic)
- [Complete Dark Mode Design Guide — UI Deploy](https://ui-deploy.com/blog/complete-dark-mode-design-guide-ui-patterns-and-implementation-best-practices-2025)
- [Dark Mode CSS Complete Guide — design.dev](https://design.dev/guides/dark-mode-css/)
- [Material Design Dark Theme Documentation](https://github.com/material-components/material-components-android/blob/master/docs/theming/Dark.md)
- [Dark Mode Typography — Design Shack](https://designshack.net/articles/typography/dark-mode-typography/)
- [Typography — Radix Themes](https://www.radix-ui.com/themes/docs/theme/typography)
- [Tailwind CSS v4 Documentation — Colors, Shadows, Transitions, Rings](https://tailwindcss.com/docs/)
- [Demystifying Tailwind Borders, Outlines, and Rings — Charlie Vuong](https://www.charlievuong.com/demystifing-tailwind-borders-outlines-and-rings)
