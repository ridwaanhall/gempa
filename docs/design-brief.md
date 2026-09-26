# Design brief — "Seismic Clay" (neumorphic redesign)

This is the working prompt for the v2.1 redesign. It was written first and then
executed; keep it as the source of truth for visual decisions.

---

## Prompt

> You are a senior FastAPI engineer and product/UI designer. Redesign the Gempa
> website (Indonesian earthquake monitor, BMKG data) so it no longer reads as a
> generic AI-generated dashboard. Use a **restrained neumorphic ("soft UI")
> language** built on an **earth/clay neutral** and the **earthquake magnitude
> palette** as the only chromatic colour. Audit every component: none may be
> left in the old style. Fix every bug and rough edge you find along the way.
> Keep the stack: FastAPI + Jinja2 + hand-written CSS + vanilla ES modules.
> No CSS frameworks, no new JS dependencies. Commit after each coherent change.

### 1. Why the current UI reads as "AI slop"

- Uppercase, letter-spaced "eyebrow" labels above every heading.
- Hairline-bordered boxes everywhere; every surface looks the same, so there is no hierarchy.
- Pills with decorative dots; grey-on-grey secondary text; a generic top-nav-plus-cards layout.
- Nothing ties the look to *seismology*: the magnitude colour is only used on tiny badges.

### 2. Direction: "Seismic Clay"

Soft, tactile, and calm. Surfaces are pressed out of one warm clay material,
like a well-made instrument. Colour appears only where it carries meaning:
magnitude, tsunami level, and live status.

Rules for neumorphism that stays usable:

1. **One material.** Page background and raised surfaces share the same base
   colour. Depth comes only from paired shadows: a light one from the top left
   and a dark one from the bottom right.
2. **Three depths only.**
   - `raised`: cards, header, and buttons at rest.
   - `inset` (pressed into the surface): inputs, tracks, wells, and the active nav item.
   - `flat`: rows inside a card.

   No nesting raised-in-raised.
3. **Contrast is not negotiable.** Text meets WCAG AA (4.5:1 body, 3:1 large and UI).
   Every interactive element also has a non-shadow cue (colour, icon, or text), and
   focus shows a 2px ring in the accent colour, because shadows alone are
   invisible to many users.
4. **Pressed state = inset.** Buttons and toggles go from raised to inset on
   `:active` / `aria-pressed="true"`, which gives a physical click.
5. Radii are generous but consistent: 22px for cards, 14px for controls, 999px for pills and tracks.

### 3. Colour tokens

| Token | Light | Dark | Use |
| --- | --- | --- | --- |
| `--clay` | `#e7e1d8` | `#23201c` | page and surface base (same) |
| `--clay-hi` | `#fffaf2` | `#2e2a25` | light shadow |
| `--clay-lo` | `#c4b9a8` | `#141210` | dark shadow |
| `--well` | `#ddd6cb` | `#1c1a17` | inset fills (inputs, tracks) |
| `--ink` | `#2a241d` | `#efe8dc` | primary text |
| `--ink-2` | `#5a5146` | `#c4baaa` | secondary text (AA on clay) |
| `--ink-3` | `#72685b` | `#9d9383` | tertiary / captions (AA on clay) |
| `--accent` | `#c2410c` | `#f07a3c` | focus ring, links, live accents (seismic orange) |
| `--m-0 … --m-7` | stone → amber → orange → vermilion → crimson → oxblood | lifted for dark | magnitude ramp |
| `--lv-awas/siaga/waspada` | crimson / vermilion / amber | same family | tsunami levels |

Magnitude is the signature. It drives the badge fill, map markers, the hero
**dial** arc, the left "fault line" accent on list rows, and chart bars.

### 4. Typography

- **Sans:** "Plus Jakarta Sans" (Indonesian-designed, warm geometric, fits the
  clay) at weights 400, 500, 600, 700.
- **Mono / numerals:** "JetBrains Mono" (tabular, legible at small sizes) for
  magnitudes, depths, coordinates and times.
- **Scale** (clamp-based): 12 / 13.5 / 15 / 17 / 20 / 26–34 / hero 64–112.
- **Headings:** sentence case, weight 700, tight tracking.
- **Labels:** 12.5px, weight 500, sentence case in `--ink-3`. Drop the uppercase eyebrows.

### 5. Layout

- **Header:** a floating *raised* bar with a 12px inset from the viewport edge, radius 22px, and sticky.
  - Brand on the left (seismograph glyph in accent).
  - Nav in the centre as an **inset track** in which the active item is a *raised* chip.
  - Live status and the theme switch on the right.
  - Below 900px the nav becomes a horizontally scrollable inset track on its own row.
- **Home (bento):**
  1. **Hero dial card.** A circular raised gauge with an SVG arc (value = magnitude / 9) coloured by the ramp, and the magnitude numeral in the centre. Next to it: region, time, and a 2×2 inset "facts wells" grid.
  2. **Map card** (large).
  3. **Four stat tiles.**
  4. **Recent detections card** with a magnitude fault-line accent per row.
  5. **Shortcut tiles** to Tsunami and Peta.
- **List pages** (realtime, felt, M5+): the page head holds the title, a one-line description and meta chips. Below that sits a toolbar card (inset search, segmented control), then a split card layout: list or table on the left, sticky map card on the right. On phones the map comes first at 42vh.
- **Tsunami:** one raised card per event. Head row: dial-less magnitude badge, title, status chip, facts wells. Body: timeline, level meters (inset tracks with coloured fills), disclosures, and a thumbnail strip.
- **Damage:** stat tiles, map card, toolbar, table card, pager.
- **Map:** a full-bleed map with a floating raised layer panel and raised Leaflet controls.
- **About:** a two-column reading layout. The API panel is a raised card with inset code wells.
- **Footer:** a quiet, flat footer with source attribution and links.
- **Width:** container max 1360px; the wide container on list pages is 1680px. Gutters
  clamp 16 → 40px. At ≥1920px the base font scales 106%.

### 6. Components (every one gets restyled — checklist)

| Component | Treatment |
| --- | --- |
| **Header / nav / brand / live / theme button** | raised bar; inset nav track; raised active chip; raised round icon buttons with an inset active state |
| **Page head** | title, description, meta *chips* (inset); no eyebrow |
| **Section head** | h2 + quiet link with an arrow |
| **Card (`.card`)** | raised, 22px radius, 24px padding (16px on mobile) |
| **Well (`.well`)** | inset fill for facts, code, stats |
| **Magnitude badge** | rounded square filled with the ramp colour, mono numeral, subtle inner highlight |
| **Dial** | SVG gauge (track = inset, arc = ramp colour, round caps), numeral centred |
| **Chips / pills** | raised small; tsunami levels are solid colour; "ok" / "signal" are tinted text with a dot only for live |
| **Facts** | 2-col (4-col wide) grid of inset wells, label above value |
| **Stat tiles** | raised tiles, big mono value, small label, note |
| **Event row** | flat row inside a card, 4px magnitude "fault line" at the left, hover = inset |
| **Buttons** | `.btn` raised → inset on press; `.btn--accent` accent-filled with a soft coloured shadow |
| **Inputs / select / search** | inset wells, focus ring |
| **Segmented control** | inset track, raised selected segment |
| **Checkbox / toggle** | custom inset box with an accent tick |
| **Table** | inside a card; sticky header on the clay; hover row inset tint; selected row gets the accent bar |
| **Pager** | raised buttons with a disabled state |
| **Map card** | raised frame with the map clipped to the radius; Leaflet zoom and layers styled raised; popups as raised cards |
| **Legend** | inline row of magnitude dots with labels |
| **Map layer panel** | raised floating card, collapsible, custom checkboxes, counts in mono |
| **Detail sheet (dialog)** | raised; bottom sheet with a grab handle on mobile; images capped |
| **Gallery / figure** | inset frame; thumbnails `aspect-ratio: 4/3`, `object-fit: cover` |
| **Timeline** | inset rail, raised dots; latest dot accent |
| **Level meters** | inset track + coloured fill |
| **Disclosure** | raised summary chip with a rotating chevron |
| **Prose (narrative, about)** | max 68ch, comfortable leading |
| **Skeleton / empty / error** | inset shimmer; empty = icon + text; error = accent-bordered well |
| **Alert banner** | full-width crimson strip, above the header |
| **Footer** | flat, muted |
| **404** | big inset numeral with a dial motif |
| **Scrollbar** | 6px thin, rounded clay thumb, transparent track (global + inner scrollers, Firefox + WebKit) |

### 7. Images at high resolution

- Shakemap in the sheet: `max-height: min(62vh, 720px)`, `width: auto`,
  `object-fit: contain`, centred on a well.
- Gallery thumbnails: fixed aspect ratio 4:3, `max-width: 240px` per tile, grid auto-fill.
- The sheet is at most 820px wide, so images never scale beyond the design at 2560px+.
- All images are `loading="lazy"` and `decoding="async"` with explicit aspect ratios to avoid CLS.

### 8. SEO

- Server-render the primary content of each page, so crawlers and no-JS readers get real text:
  - home: the latest earthquake;
  - felt / M5+ lists;
  - realtime table rows;
  - tsunami event summaries;
  - the first page of damage rows.
- Embed the same data as `<script type="application/json">` so JS hydrates without a second request or a skeleton flash.
- Dynamic home `<title>` and description that include the latest magnitude and region.
- Open Graph and Twitter tags complete (`og:image` 1200×630 PNG with width, height and alt; `twitter:title/description/image`).
- JSON-LD: `WebSite` + `Organization` (publisher), `WebPage`, `BreadcrumbList`, and a `Dataset` on the About page describing the API.
- `sitemap.xml` with `lastmod`, `robots.txt`, canonical URLs, `lang="id"`, a sensible heading order (one `h1` per page), and descriptive link text.

### 9. Bugs and rough edges to fix

- M5+ / felt maps fit to the bounds of far-away events; limit to Indonesia and pad.
- Refreshes run twice when the tab regains visibility (timer and visibility handler).
- The home action buttons wrap awkwardly; the hero feels empty on wide screens.
- The realtime history shows HH.MM only; show seconds.
- Relative times like "bulan lalu" need the date next to them.
- Leaflet controls and popups don't match the theme.
- Inner scroll areas have default scrollbars.

### 10. Definition of done

- Every page works at 360, 768, 1024, 1440 and 2560px in light and dark mode, with no horizontal scroll.
- `uv run pytest` and `uv run ruff check .` pass; JS modules parse.
- `AGENTS.md` documents the design system rules.
