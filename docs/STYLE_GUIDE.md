# Frontend Style Guide — Chroma Design System

> Direct reference from trychroma.com. Use these exact values for pixel-perfect replication.

---

## 1. Philosophy

Chroma's design is **ultra-minimalist typographic modernism**. The page uses:
- Exactly 3 colors: black (`#070707`), white (`#ffffff`), one gray (`#f6f6f6`)
- No gradients, no drop shadows, no decorative elements
- Typography IS the decoration
- Content width is unconstrained (`max-width: none`) — responsive padding handles margins
- Each page section is separated by whitespace, not dividers

---

## 2. Color Palette

| Token | Value | Usage |
|-------|-------|-------|
| `--color-bg` | `#ffffff` | Page background |
| `--color-muted` | `#f6f6f6` | Alternate section backgrounds (metrics, interactive demo) |
| `--color-border` | `#e8e8e8` | All borders, dividers, input outlines |
| `--color-fg` | `#070707` | Primary text (headings, body) |
| `--color-muted-fg` | `#7b7b7b` | Secondary text (captions, subtitles, footer links) |
| `--color-primary` | `#141414` | Primary CTA buttons (bg), interactive elements |
| `--color-primary-fg` | `#ffffff` | Text on primary buttons |
| `--color-success` | `#4ade80` | Planet confirmation badge |
| `--color-warning` | `#eab308` | Candidate/borderline badge |
| `--color-error` | `#ef4444` | False positive badge, error toasts |

---

## 3. Typography

### Fonts
- **Headings + Body**: Inter (variable 100-900) — loaded via `@next/font`
- **Code**: IBM Plex Mono (400, 500, 600)
- **Fallback**: Inter Fallback, IBM Plex Mono Fallback

### Size Scale

```css
/* Heading scale */
--text-hero:    24px / 36px  weight: 400  /* H1 — Hero title */
--text-sub:     16px / 24px  weight: 400  /* H2 — Subtitle/description */
--text-body:    16px / 24px  weight: 400  /* Body paragraphs */
--text-sm:      14px / 20px  weight: 400  /* Small text, button labels */
--text-xs:      13px / 16px  weight: 400  /* Tiny captions, chip labels */
--text-tiny:    12px / 16px  weight: 400  /* Legal, timestamps */
```

### Font Weights (used on Chroma)
- `400` (normal) — all body text, hero heading
- `500` (medium) — section headings, hidden accessibility headings
- `600` (semibold) — footer column headings

### Letter Spacing
- Normal: `normal` (hero, body)
- Wide: `0.025em` (sparingly)
- Wider: `0.05em`

---

## 4. Spacing & Layout

### Navigation Bar
```
Height: 73px
Position: fixed, top: 0
Background: transparent (no backdrop blur)
Border-bottom: 1px solid #e8e8e8
Padding: 0 24px (responsive)
Logo: 98×24px (SVG wordmark)
```

### Section Spacing
```
Between major sections: 80-120px gap (controlled by section padding)
Section padding: py-16 md:py-24 (Tailwind)
Content max-width: none (full width with px-6 md:px-12)
```

### Grid
```css
main { display: grid; gap: normal; }  /* sections stack vertically */
```

### Cards
```
No card background on Chroma homepage (transparent)
Interactive demo card: white bg (#fff) in a gray section
Border-radius: 8px (all interactive elements)
```

---

## 5. Components

### 5.1 Primary Button (CTA)
```
Background: #141414 (black)
Text: #ffffff
Border: none
Border-radius: 8px
Padding: 8px 16px (varies by context)
Font: 14-16px, weight 500
Hover: opacity-90
Cursor: pointer
```

### 5.2 Secondary Button
```
Background: transparent
Text: #070707
Border: 1px solid transparent (or none)
Border-radius: 6-8px
Padding: 0px 10px (or 8px 16px)
Font: 14-16px, weight 500
Hover: underline (or bg-muted)
```

### 5.3 Navigation Tabs (like Agent/Search)
```
Active tab: Background #000, Text white
Inactive tab: Background transparent, Text #070707
Height: auto
Border-radius: 6px (inner tab shape)
Container: white bg, rounded-8px, padding 4px
```

### 5.4 Input / Textbox
```
Background: transparent
Border: none (visible in context of card)
Font: 16px
Placeholder: #7b7b7b
Padding: standard
```

### 5.5 Stat / Metric Cards
```
Minimal — no background/border unless in a gray section
Label: muted-fg (#7b7b7b), 14px
Value: fg (#070707), 24px, bold 600
Icon: inline SVG, 24×24px, positioned left
Layout: flex row (icon | value + label column)
```

### 5.6 Feature/Icon Grid Items
```
Icon: 20-24px (or unicode symbols for demo)
Title: fg, 16px, 500 weight
Description: muted-fg, 14px
Hover: subtle effect (cursor pointer)
Layout: column (icon, title, desc) or row
```

### 5.7 Code Block
```
Background: (part of layout context)
Font: IBM Plex Mono, 13-14px
Border-radius: 6-8px
Copy button: top-right corner, icon only
```

---

## 6. Interactive Demo Section (Reference)

Chroma has an interactive search demo on their homepage. For this project, we don't need an interactive demo — but the card aesthetic carries over:

```
Container: white bg (#ffffff), rounded-8px
Tab bar: flex row, 2 tabs (Agent | Search)
Active tab: black bg
Content area: 2-column layout (chat | results/terminal)
```

---

## 7. Responsive Behavior

Chroma uses minimal responsive breakpoints:
- **Mobile**: Single column, stacked sections
- **Tablet (md:)**: 2-column grids appear
- **Desktop**: Full layout, max 3-4 column grids

Key patterns:
- Hero heading stays 24px at all breakpoints
- Section padding increases on desktop (`md:py-24`)
- Grid columns change count but gaps stay consistent
- Navigation collapses to hamburger on small screens (implied by structure)

---

## 8. Animation Guidelines

Chroma uses extremely subtle animations:
- **Hover**: `opacity-90` on buttons (not a separate hover state)
- **Entrance**: Page content loads static — no fade-in/animate-on-scroll
- **Interactive demo**: Tab switch is instant, no transition
- **No loading spinners** — static content only (except the data-upload processing step, which needs its own animation)

For the data upload app, add ONLY:
- Upload progress: thin animated bar (not a spinner)
- Processing steps: sequential checkmark animation (green fill)
- Toast: slide-in from top-right, 300ms ease
- Chart: Plotly's built-in render animation (keep)

---

## 9. Component Spacing Reference

| Element | Spacing |
|---------|---------|
| Section padding (top/bottom) | 64px (py-16) → 96px (md:py-24) |
| Between heading and content | 20px (mt-5) |
| Between CTA buttons | 12px gap |
| Between metric cards | 24px gap |
| Grid gap (charts) | 24px |
| Between nav items | 24px |
| Footer column gap | 48px |
| Content padding (sides) | 24px (px-6) → 48px (md:px-12) |
