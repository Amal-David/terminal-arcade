# Terminal Arcade

A collection of terminal-based games and apps built with Python and curses.

![Dino Run — Gameplay](assets/screenshots/dino_gameplay.png)

## Games

### Dino Run

An endless runner with 10 selectable dinosaurs, 3 rotating biomes, a charge-based roar mechanic, and retro audio.

![Dino Run — Title Screen](assets/screenshots/dino_title.png)

[Read more →](dino_game/README.md)

### The Bookshelf

A terminal book discovery app with 313 books across motivation, startup, and romance genres. Browse, search, collect favorites, and explore quotes.

![The Bookshelf — Browse](assets/screenshots/bookshelf_browse.png)

[Read more →](bookshelf/README.md)

## Requirements

- Python 3.10+
- A terminal with curses support (most Unix terminals, macOS Terminal, iTerm2)
- macOS for audio playback (optional — game works without sound)

## Install

```bash
git clone https://github.com/Amal-David/terminal-arcade.git
cd terminal-arcade
pip install -e .
```

## Run

```bash
# Dino Run
dino-run
# or: python3 -m dino_game

# The Bookshelf
bookshelf
# or: python3 -m bookshelf
```

## Test

```bash
python3 -m unittest discover -s tests -v
```

## License

[MIT](LICENSE)
