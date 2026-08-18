# nette brand

The single source of truth for nette's visual identity. Agents and humans
producing any visual artifact (docs, terminal output, social images, site
later) start here.

## Logo

The mark is three indented code lines validated by an orange check: readable
structure, verified. Files live in [`assets/`](../assets/).

| File | Use |
|------|-----|
| `assets/logo-dark.svg` | On dark backgrounds (primary context) |
| `assets/logo-light.svg` | On light backgrounds |
| `assets/icon.svg` | App icon, favicon source, avatars (512, orange gradient) |

Rules: never distort, never recolor the check outside the palette, keep clear
space equal to the height of one code line around the mark.

## Palette

Zinc neutrals + one orange accent. The orange is scarce on purpose: when you
see it, it means something (a finding, an action, the brand).

| Token | Hex | Use |
|-------|-----|-----|
| `bg` | `#09090b` | Page and terminal background |
| `surface` | `#111114` | Cards, panels |
| `border` | `#26262a` | Hairlines, dividers |
| `text` | `#e4e4e7` | Primary text |
| `muted` | `#a1a1aa` | Secondary text |
| `faint` | `#71717a` | Tertiary text, prompts |
| `orange` | `#f97316` | Accent. Findings, CTAs, active states |
| `orange-hi` | `#fb923c` | Gradient start, highlights on dark |
| `orange-lo` | `#ea580c` | Gradient end |
| `cream` | `#fff7ed` | Warm white on orange surfaces; file paths in terminal |
| `green` | `#4ade80` | Success only |

Gradient: `linear-gradient(120deg, #fb923c, #ea580c)`. Reserved for hero
moments (app icon, social cards). Never in terminal output.

**Banned: blue.** No blue anywhere in the identity or terminal output.

## Typography

| Role | Typeface | Weights | Source |
|------|----------|---------|--------|
| Display / UI | [Satoshi](https://www.fontshare.com/fonts/satoshi) | 400, 500, 700, 900 | Fontshare (free) |
| Code / terminal | [Monaspace Neon](https://monaspace.githubnext.com/) | 400, 500 | GitHub Next (OFL) |

Satoshi is the human voice (prose, headings). Monaspace is the machine voice
(code, findings, CLI). The boundary between the two is nette's subject.

Display headings: weight 900, letter-spacing -0.03em. Body: 400/500. Never
fake-bold Monaspace.

## Terminal output

The terminal is nette's primary UI. Reference implementation: Python
[`rich`](https://github.com/Textualize/rich).

| Element | Color | Style |
|---------|-------|-------|
| Prompt `$` | `faint` | |
| Command | `text` | |
| Finding marker `✗` | `orange` | bold |
| File path + line | `cream` | bold |
| Finding message | `muted` | |
| Success marker `✓` | `green` | bold |
| Summary counts | `faint` | |

Example (colors annotated):

```text
$ nette check
✗ services/booking.py:42  function does 3 things: extract validate_fare and persist_order
✗ routers/search.py:118   narrative comment restates the code below it
✓ 14 files clean · 2 findings · 0.4s
```

`✗` orange, `services/booking.py:42` cream bold, message muted, `✓` green,
tail faint. No other colors. No blue, ever.

Principles:

1. One finding per line, scannable in a glance.
2. The path is the anchor: brightest element after the marker.
3. Color carries meaning only (finding, success, brand). Decoration is noise.
4. Output must stay legible with colors stripped (CI logs, pipes).

## Voice

See [.ai/writing.md](../.ai/writing.md). Short version: direct, concrete,
zero slop. The tagline pattern is two short sentences: "AI writes code.
nette keeps it clean."
