# Polyglot Launch — Visual Identity

## Style Prompt

A 30-second cabinet-style promo for Polyglot — the language-learning ambient hook for Claude Code and Codex. Aesthetic blends a developer terminal (dark navy canvas, monospace, scanline glow, ASCII edges) with synthwave neon accents (cyan / magenta / yellow). The pace is brisk, the typography is confident and large, and every scene has the texture of a terminal that's also a window into the rest of the world (a CJK character glowing through, an Arabic phrase wrapping right-to-left, a Devanagari headline floating above a Bash prompt). The feeling: "your IDE is now a passport".

## Colors

| Role                | Hex       | Use                                        |
|---------------------|-----------|--------------------------------------------|
| canvas              | `#0b0d1a` | Page background                            |
| panel               | `#13162a` | Card / terminal panel background           |
| panel-deep          | `#0f1124` | Inner inset panel                          |
| primary (cyan)      | `#5eead4` | Headlines, primary accents, prompt cursor  |
| magenta             | `#f472b6` | Sub-label, pair direction arrow, transit   |
| yellow              | `#fde047` | Hot accent — active state, numbers, glow   |
| green (success)     | `#86efac` | "Installed" badge, success ticks           |
| text-primary        | `#f1f5f9` | Body, target-language phrase text          |
| text-secondary      | `#94a3b8` | Pronunciation hints, dim labels            |
| text-muted          | `#475569` | Prompt scaffolding, low-priority lines     |

WCAG: every body-text-on-canvas combo above passes 4.5:1.

## Typography

- **Display** (titles, hero text): `'Space Grotesk', 'Inter', system-ui, sans-serif` — 110–180px, weight 700, tight letter-spacing.
- **Mono** (terminal, code, language phrases): `'JetBrains Mono', 'Fira Code', 'Menlo', monospace` — 28–64px, weight 500. Used everywhere a phrase, pinyin, or command is shown so non-Latin scripts get faithful rendering.

## Motion Rules

- Hero entrances: `gsap.from()` with `y: 60, opacity: 0`, `duration: 0.6-0.8`, `ease: "power3.out"`.
- Numbers / stats: `power2.out` with a 200ms stagger across siblings.
- Phrase cards in the variety scene swap with a quick `expo.out` slide + fade (220ms each).
- Scene transitions: 350ms crossfade with a slight upward drift on the outgoing scene.

## What NOT to Do

- No bright pure-white backgrounds. Polyglot is a terminal product.
- No `#3b82f6`, `#10b981`, generic Bootstrap blue, or any of the default Tailwind defaults — use the palette above.
- No Roboto, no Helvetica, no Times. Display sans only for headlines; everything that represents a phrase or command stays in JetBrains Mono so non-Latin glyphs render correctly.
- No emoji-heavy frames. The 🌍 globe is used sparingly as the cabinet mark; everything else is typographic.
- No fast-flashing strobes. The variety scene swaps phrases on a calm 0.9s cadence — readable, not seizure-inducing.
