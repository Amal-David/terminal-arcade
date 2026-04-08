# Dino Run

Dino Run is a terminal endless runner with a selectable roster of ten dinosaur runners, three rotating biome themes, a charge-based roar move, and lightweight retro audio.

## Requirements

- Python 3.10+
- A terminal with `curses` support
- macOS for built-in audio playback via `afplay`

## Run

From the repo root:

```bash
python3 -m dino_game
```

The old launcher still works too:

```bash
python3 dino-game/dino.py
```

If you want an installed command while developing locally:

```bash
python3 -m pip install -e .
dino-run
```

## Controls

- Title screen: `Left` / `Right` or `1`-`0` to choose a dinosaur
- `Space` or `Up`: jump
- `Down`: duck or fast-fall
- `X`: roar burst when the meter is full
- `P`: pause
- `Enter` or `Space`: restart after a crash
- `Q` or `Esc`: quit

## SVG Asset Pipeline

The default `Tyrant Rex` is generated from the SVG source asset at [assets/source/dinosaur_svg_sprite_animation.svg](/Users/amal/experiments/terminal-games/assets/source/dinosaur_svg_sprite_animation.svg). The build script rasterizes that SVG with ImageMagick and converts the result into terminal Unicode frames used by the game.

To rebuild the generated terminal frames:

```bash
python3 scripts/generate_dino_svg_assets.py
```

This writes [generated_svg_frames.py](/Users/amal/experiments/terminal-games/dino_game/generated_svg_frames.py).

## What Changed From The Prototype

- The game now ships with ten selectable dinosaur silhouettes instead of one fixed hero.
- Runs rotate through `Scrub Desert`, `Fern Grove`, and `Basalt Night`.
- Speed ramps more aggressively and is tied to score milestones.
- Fragile hazards can be broken with the roar burst.
- Audio now includes a looping gameplay track plus event-driven sound effects.
- High score is saved locally between runs.

## Audio Assets

Audio files are generated from the repo with:

```bash
python3 scripts/generate_audio_assets.py
```

## Test

```bash
python3 -m unittest discover -s tests -v
```
