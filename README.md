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

## Claude Code Ambient Quotes

This repo includes a PostToolUse hook for [Claude Code](https://claude.ai/code) that delivers contextually relevant book quotes during your coding sessions.

### Install

1. Clone the repo:
   ```bash
   git clone https://github.com/Amal-David/terminal-arcade.git
   ```

2. Add to your `~/.claude/settings.json` (merge with existing hooks if you have any):
   ```json
   {
     "hooks": {
       "PostToolUse": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "python3 /path/to/terminal-arcade/bookshelf/skill/hook.py",
               "timeout": 5
             }
           ]
         }
       ]
     }
   }
   ```

3. Replace `/path/to/terminal-arcade` with the actual clone location.

Every few tool calls, you'll get a quote matched to your coding context — debugging gets perseverance quotes, shipping gets courage quotes, and so on.

**Configure** (optional) at `~/.config/bookshelf/config.json`:
```json
{
  "quote_cadence": 5,
  "context_matching": true
}
```

## Test

```bash
python3 -m unittest discover -s tests -v
```

## License

[MIT](LICENSE)
