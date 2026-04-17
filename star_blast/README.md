# Star Blast

A Nokia-inspired side-scrolling terminal shooter with a short campaign, an endless mode, and a small arcade HUD.

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
| `Up` / `W` | Move up |
| `Down` / `S` | Move down |
| `Space` | Fire |
| `P` | Pause / Resume |
| `A` / `D` / `←` / `→` | Change mode on title screen |
| `1` / `2` | Pick Campaign / Endless |
| `Enter` / `Space` / `R` | Start / Restart |
| `Q` / `Esc` | Quit |

## Modes

- **Campaign** — 3 short stages with escalating enemy pressure and a carrier boss at the end of each stage
- **Endless** — survival mode with steadily faster spawn pacing and tougher enemy mixes

## Enemy Types

- `*` Debris — slow, disposable hazards
- `>` Scout — fast basic ships
- `Z` Zigzag — weaving enemies that drift vertically
- `H` Turret — armored shooters that fire straight bolts
- `<M>` Carrier — stage boss with burst fire and high health

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
