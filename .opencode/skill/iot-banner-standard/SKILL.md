---
name: iot-banner-standard
description: Use ONLY when creating or reviewing the repository banner (the <repo>.png logo referenced at the top of the README) of a picokit lesson repo. Enforces the fixed dark terminal-style hacker theme rendered from banner.json by gen_banner.py at 2400x2400, strictly symmetric about the vertical center line, unique per project by accent color, icon, layout, and copy, with every element in its own band so nothing overlaps, auto-fitted so no text ever overflows, and referenced by the exact raw GitHub URL. No exceptions and no variation in theme between projects.
---

# IoT banner standard

Every project ships a `<repo>.png` banner at the repository root and references
it from the first line of the README. The artwork is generated, never hand
drawn, so the theme is identical across the series while the content is unique.

## The fixed theme

Every banner is a 2400x2400 dark terminal poster with an accent-tinted radial
background, a vignette, a glowing eyebrow, a gradient title, a subtitle, a
circular icon medallion, a terminal transcript, data chips, category pills,
status cards, and a dotted footer. The exact arrangement depends on the chosen
`layout`, but the palette, fonts, and mood never change.

## Symmetry and no-overlap rule

The composition is symmetric about the vertical center line (x = 1200): every
centered element is centered on that axis, and the medallion, pills, chips,
cards, terminal, and footer are mirrored or evenly distributed. Each element
occupies its own fixed horizontal band with a gap, so no two elements can
overlap. The icon is drawn inside the medallion ring at a radius derived from a
per-icon reach factor, so no ray, arc, or leg can cross the ring or any frame.

## Auto-fit rule

No glyph may ever cross the image bounds. Every centered line (eyebrow, title,
subtitle, panel status, category row, and both footer lines) is measured at
render time; the letter tracking is reduced to zero first and then the font
size is reduced until the line fits inside an 80 px inset on each side. Terminal
lines and chip/card/pill text are likewise shrunk to fit their frames.

## The spec

`banner.json` at the repository root drives the render. Required keys:
`repo`, `eyebrow`, `title`, `subtitle`, `accent`, `bg`, `icon`, `layout`,
`panel_status`, `chips`, `terminal`, `categories`, `cards`, `footer`. Optional
keys: `dim`, `white`, `cyan`, `bg_edge`, `stat`.

- `icon` is one of: `thermo`, `leaf`, `drop`, `led`, `lcd`, `servo`, `button`,
  `remote`, `antenna`, `lock`, `shield`, `bug`, `chip`, `key`, `clock`, `gauge`,
  `wifi`, `hash`, `wave`, `bell`.
- `layout` is one of: `panel`, `split`, `terminal`, `stat`, `grid`.
- `stat` is the huge centered reading used by the `stat` layout; when absent the
  first chip value is used.

Pick one accent color per project so the series is a rainbow of the same
design, and never repeat an accent+icon+layout triple. Keep the background a
near-black tint of the accent.

## Generate

```bash
python3 .opencode/skill/iot-banner-standard/gen_banner.py
```

This writes `<repo>.png` at the repository root. The README first line must be
exactly:

```
![<repo>](https://raw.githubusercontent.com/mytechnotalent/<repo>/main/<repo>.png)
```

## Verify

```bash
python3 .opencode/skill/iot-banner-standard/validate_banner.py
```

Exit 0 is clean; any output is a failure and must be fixed before the change is
complete. Validation also re-measures every drawn text line and fails if any
line falls outside the `[80, 2320]` safe inset or crosses the image bounds.
