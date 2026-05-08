# Star Blast

A large-sprite vertical terminal shooter with a full-size starship, asteroid obstacles, enemy ships, turret platforms, carrier bosses, punchier blast/impact effects, CC0 sci-fi sound effects, a short campaign, and an endless mode.

## Run

```bash
# From the repo root
python3 -m star_blast

# Or install and run anywhere
pip install -e .
star-blast
```

## Controls

| Key | Action |
|---|---|
| `Left` / `A` | Move left |
| `Right` / `D` | Move right |
| `Space` | Fire, or hold for repeated shots on terminals with key repeat |
| `F` | Toggle autofire on / off |
| `P` | Pause / Resume |
| `A` / `D` / `←` / `→` | Change mode on title screen |
| `1` / `2` | Pick Campaign / Endless |
| `Enter` / `Space` / `R` | Start / Restart |
| `Q` / `Esc` | Quit |

## Modes

- **Campaign** — 3 short stages with escalating asteroid fields, enemy pressure, and a carrier boss at the end of each stage
- **Endless** — survival mode with steadily faster spawn pacing and tougher obstacle/enemy mixes

## Enemy Types

- `<###>` Debris — slow asteroid obstacles
- `<[V]>` Scout — fast basic ships
- `<-W->` Zigzag — weaving enemies that drift across lanes
- `[###]` Turret — armored shooter platforms that fire straight bolts
- `/MMMM\` Carrier — large stage boss with burst fire and high health

## Scoring

- Debris: +10
- Scout: +20
- Zigzag: +20
- Turret: +50
- Carrier: +250
- Campaign boss clear bonus: +100

## Audio

Star Blast plays optional sound effects for laser fire, enemy explosions, carrier blasts, menu feedback, and ship impacts. Audio playback uses `afplay` on macOS or `ffplay` when available; the game runs silently if neither player is installed.

The bundled Star Blast sound effects come from [Kenney Sci-fi Sounds](https://kenney.nl/assets/sci-fi-sounds), licensed under [Creative Commons CC0](https://creativecommons.org/publicdomain/zero/1.0/). See [`assets/audio/star_blast/LICENSE.txt`](../assets/audio/star_blast/LICENSE.txt) for the local notice.

High scores are stored locally in `star-blast/scores.json` under your platform app-data directory.

## License

[MIT](../LICENSE)
