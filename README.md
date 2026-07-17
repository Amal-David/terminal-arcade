# Terminal Arcade

A retro arcade for your terminal — pure Python, zero dependencies, curses-based. Six fully playable games and three ambient companions share one launcher: **Bookshelf**, **Wonder**, and **Polyglot**, with 70 language pairs for learning while you work. Drop-in **Claude Code** and **Codex** hooks can surface a curated book quote, a daily wonder, or a language phrase every Nth tool call — configurable cadence (5 / 10 / 20) so the wisdom lands without breaking your flow.

```bash
python3 -m bookshelf.skill.cadence 10   # one quote per 10 tool calls
```

**Topics:** `python` · `terminal` · `curses` · `arcade` · `retro-games` · `games` · `cli` · `claude-code` · `codex` · `bookshelf` · `polyglot` · `language-learning` · `ascii-art` · `chiptune`

![Arcade Launcher](assets/screenshots/arcade_launcher.png)

## Games

### Star Blast

A large-sprite terminal space shooter with a full-size ship, asteroid obstacles, enemy craft, carrier bosses, punchier blast/impact effects, CC0 sci-fi SFX, campaign stages, and endless survival.

![Star Blast — Gameplay](assets/screenshots/star_blast_gameplay.png)

[Read more →](star_blast/README.md)

### Terminal Kombat

An original large-sprite 16-bit terminal fighter with selectable warriors, CPU pressure, best-of-three rounds, jumps, crouches, throws, sweeps, blocking, meter, specials, and finishers.

```bash
python3 -m kombat_game              # or: terminal-kombat
```

[Read more →](kombat_game/README.md)

### Dino Run

An endless runner with 10 selectable dinosaurs, 3 rotating biomes, a charge-based roar mechanic, and retro audio.

![Dino Run — Gameplay](assets/screenshots/dino_gameplay.png)

[Read more →](dino_game/README.md)

### Snake

Classic Nokia snake for your terminal. Wall collisions, speed progression, and bonus food.

![Snake — Gameplay](assets/screenshots/snake_gameplay.png)

[Read more →](snake_game/README.md)

### Tetris

Classic endless block stacking with standard wall kicks, one next-piece preview, and level-based speed-up.

![Tetris — Gameplay](assets/screenshots/tetris_gameplay.png)

[Read more →](tetris_game/README.md)

### Chess

Play White against a built-in rule-based engine on a full-screen pixel-art board with easy, medium, and hard difficulty levels.

![Chess — Gameplay](assets/screenshots/chess_gameplay.png)

[Read more →](chess_game/README.md)

## Ambient companions

### The Bookshelf

A terminal book discovery app with 983 books across eight genres: fiction, history, motivation, philosophy, psychology, romance, science, and startup. Browse, search, collect favorites, and explore quotes.

![The Bookshelf — Browse](assets/screenshots/bookshelf_browse.png)
![The Bookshelf — Detail](assets/screenshots/bookshelf_detail.png)

The ambient hook surfaces a curated quote every Nth tool call — inline in your Claude Code or Codex session:

![The Bookshelf — Ambient Hook](assets/screenshots/bookshelf_ambient_hook.png)

[Read more →](bookshelf/README.md)

### Wonder

Pick a mood — funny, heartwarming, weird, or inspiring — and pull one fresh fact or story from the internet for the day. Caches the day's pick so re-opens are instant, falls back to a bundled curated set when offline. Doubles as a Claude Code + Codex ambient hook (once daily by default).

```bash
python3 -m wonder              # or: wonder
```

[Read more →](wonder/README.md)

### Polyglot

Pick one of 70 language pairs and Polyglot installs a Claude Code + Codex hook that surfaces a phrase from that pair every Nth tool call — at least 250 items per pair (more than 18,000 total). Switching pairs never re-edits `settings.json`; only the active-pair config flips.

![Polyglot — Ambient Hook](assets/screenshots/polyglot_ambient_hook.png)

```bash
python3 -m polyglot                          # or: polyglot   — opens the 70-pair cabinet
python3 -m polyglot.skill.installer status   # see what's installed and which pair is active
python3 -m polyglot.skill.cadence 10 --both  # one phrase per 10 events on both Claude and Codex
```

[Read more →](polyglot/README.md)

## Requirements

- Python 3.10+
- macOS or Linux with a curses-capable terminal
- macOS for audio playback (optional — game works without sound)
- Windows is not currently supported.

## Install

```bash
git clone https://github.com/Amal-David/terminal-arcade.git
cd terminal-arcade
pip install -e .
```

### `error: externally-managed-environment` (Homebrew Python, PEP 668)

Newer Pythons (e.g. Homebrew's `python@3.13` / `python@3.14`) refuse a bare `pip install` to protect the system install. Either use `pipx`, a venv, or pass `--user --break-system-packages`:

```bash
# Option A — pipx (recommended; isolates the install)
brew install pipx
pipx install -e .

# Option B — venv
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# Option C — user install with the override
pip install --user --break-system-packages -e .
```

### `command not found: arcade` after install

`pip` writes the launchers (`arcade`, `dino-run`, `snake-game`, `tetris`, `chess-game`, `star-blast`, `terminal-kombat`, `bookshelf`, `wonder`, `polyglot`) into Python's user-script directory, which is **not on `PATH` by default** on macOS. Add it permanently:

```bash
# macOS / Linux — add to ~/.zshrc (or ~/.bashrc) and reload your shell
echo 'export PATH="$(python3 -m site --user-base)/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

User script directories:

| OS | Script directory |
|---|---|
| macOS | `$(python3 -m site --user-base)/bin` |
| Linux | `$(python3 -m site --user-base)/bin` |

Prefer not to touch `PATH`? Run the modules directly instead — this always works after `pip install -e .`:

```bash
python3 -m terminal_arcade   # full launcher (or: arcade)
python3 -m dino_game
python3 -m snake_game
python3 -m tetris_game
python3 -m chess_game
python3 -m star_blast
python3 -m kombat_game
python3 -m bookshelf
python3 -m wonder
python3 -m polyglot
```

## Run

The module form (`python3 -m ...`) always works after `pip install -e .`. The short script names (`arcade`, `dino-run`, etc.) only work if the user script directory is on your `PATH` — see the install notes above if `command not found`.

```bash
# Full arcade launcher (recommended — always works)
python3 -m terminal_arcade
# or, if user scripts are on PATH: arcade

# Direct shortcuts

# Dino Run
python3 -m dino_game        # or: dino-run

# Snake
python3 -m snake_game       # or: snake-game

# Tetris
python3 -m tetris_game      # or: tetris

# Chess
python3 -m chess_game       # or: chess-game

# Star Blast
python3 -m star_blast       # or: star-blast

# Terminal Kombat
python3 -m kombat_game      # or: terminal-kombat

# The Bookshelf
python3 -m bookshelf        # or: bookshelf

# Wonder
python3 -m wonder           # or: wonder

# Polyglot
python3 -m polyglot         # or: polyglot
```

## Test

```bash
python3 -m unittest discover -s tests -v
```

## License

[MIT](LICENSE)
