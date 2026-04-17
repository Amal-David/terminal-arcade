# Star Blast

A Nokia-inspired vertical terminal shooter with a larger starship sprite, chunkier enemy ships, a tighter playfield, a short campaign, and an endless mode.

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

- **Campaign** — 3 short stages with escalating enemy pressure and a carrier boss at the end of each stage
- **Endless** — survival mode with steadily faster spawn pacing and tougher enemy mixes

## Enemy Types

- `[#]` Debris — slow, disposable hazards
- `[V]` Scout — fast basic ships
- `<W>` Zigzag — weaving enemies that drift across lanes
- `[###]` Turret — armored shooters that fire straight bolts
- `/MMM\` Carrier — stage boss with burst fire and high health

## Scoring

- Debris: +10
- Scout: +20
- Zigzag: +20
- Turret: +50
- Carrier: +250
- Campaign boss clear bonus: +100

High scores are stored locally in `star-blast/scores.json` under your platform app-data directory.

## License

[MIT](../LICENSE)
