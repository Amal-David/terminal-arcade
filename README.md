# Terminal Arcade

A retro arcade for your terminal — pure Python, zero dependencies, curses-based. Six fully-playable games and an interactive bookshelf, all behind a single launcher. Plus drop-in **Claude Code** and **Codex** hooks that surface a curated book quote every Nth tool call — configurable cadence (5 / 10 / 20) so the wisdom lands without breaking your flow.

```bash
python3 -m bookshelf.skill.cadence 10   # one quote per 10 tool calls
```

**Topics:** `python` · `terminal` · `curses` · `arcade` · `retro-games` · `games` · `cli` · `claude-code` · `codex` · `bookshelf` · `ascii-art` · `chiptune`

![Arcade Launcher](assets/screenshots/arcade_launcher.png)

## Games

### Star Blast

A large-sprite terminal space shooter with a full-size ship, asteroid obstacles, enemy craft, carrier bosses, punchier blast/impact effects, CC0 sci-fi SFX, campaign stages, and endless survival.

![Star Blast — Gameplay](assets/screenshots/star_blast_gameplay.png)

[Read more →](star_blast/README.md)

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

### The Bookshelf

A terminal book discovery app with 313 books across motivation, startup, and romance genres. Browse, search, collect favorites, and explore quotes.

![The Bookshelf — Browse](assets/screenshots/bookshelf_browse.png)
![The Bookshelf — Detail](assets/screenshots/bookshelf_detail.png)

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

If `pip` warns that `arcade`, `dino-run`, `snake-game`, `tetris`, `chess-game`, `star-blast`, or `bookshelf` were installed to a directory that is not on `PATH`, you can either run the modules directly or add the user script directory to `PATH`.

User script directories:

| OS | Script directory |
|---|---|
| macOS | `$(python3 -m site --user-base)/bin` |
| Linux | `$(python3 -m site --user-base)/bin` |
| Windows | `$(py -m site --user-base)\Scripts` |

Examples:

```bash
# macOS / Linux: temporary PATH update for the current shell
export PATH="$(python3 -m site --user-base)/bin:$PATH"

# macOS / Linux: run without touching PATH
python3 -m terminal_arcade
python3 -m dino_game
python3 -m snake_game
python3 -m tetris_game
python3 -m chess_game
python3 -m star_blast
python3 -m bookshelf
```

```powershell
# Windows PowerShell: temporary PATH update for the current session
$env:Path = "$(py -m site --user-base)\Scripts;$env:Path"

# Windows: run without touching PATH
py -m terminal_arcade
py -m dino_game
py -m snake_game
py -m tetris_game
py -m chess_game
py -m star_blast
py -m bookshelf
```

## Run

The module form (`python3 -m ...`) always works after `pip install -e .`. The short script names (`arcade`, `dino-run`, etc.) only work if the user script directory is on your `PATH` — see the install notes above if `command not found`.

```bash
# Full arcade launcher (recommended — always works)
python3 -m terminal_arcade
# or, if user scripts are on PATH: arcade
# Windows: py -m terminal_arcade

# Direct shortcuts

# Dino Run
python3 -m dino_game        # or: dino-run        # Windows: py -m dino_game

# Snake
python3 -m snake_game       # or: snake-game      # Windows: py -m snake_game

# Tetris
python3 -m tetris_game      # or: tetris          # Windows: py -m tetris_game

# Chess
python3 -m chess_game       # or: chess-game      # Windows: py -m chess_game

# Star Blast
python3 -m star_blast       # or: star-blast      # Windows: py -m star_blast

# The Bookshelf
python3 -m bookshelf        # or: bookshelf       # Windows: py -m bookshelf
```

## Claude Code Ambient Quotes

A PostToolUse hook for [Claude Code](https://claude.ai/code) that delivers contextually relevant book quotes during your coding sessions. After every few tool calls, a quote appears — matched to what you're doing.

![Ambient Quote Hook](assets/screenshots/ambient_quote_hook.png)

### Quick Start

**Requirements:** Python 3.10+, Claude Code (CLI, desktop app, or IDE extension)

**Step 1.** Clone and install:

```bash
git clone https://github.com/Amal-David/terminal-arcade.git
cd terminal-arcade
pip install -e .
```

> The `pip install -e .` step is required — the hook imports the bookshelf data module.

**Step 2.** Open `~/.claude/settings.json` and add the hook.

If you **don't have any hooks yet**, add this to your settings:

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

If you **already have hooks**, just add a new entry to the existing `PostToolUse` array:

```json
{
  "hooks": {
    "PostToolUse": [
      { "hooks": [{ "type": "command", "command": "your-existing-hook" }] },
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

**Step 3.** Replace `/path/to/terminal-arcade` with the actual path where you cloned the repo.

**Step 4.** Restart Claude Code. Quotes will start appearing after every few tool calls.

This works everywhere Claude Code runs — the CLI (`claude`), the desktop app, and VS Code / JetBrains extensions. They all share `~/.claude/settings.json`.

### Configuration

Optionally tweak the hook behavior by creating a config file:

| Platform | Config path |
|----------|-------------|
| macOS | `~/Library/Application Support/bookshelf/config.json` |
| Linux | `~/.local/share/bookshelf/config.json` |
| Windows | `%APPDATA%/bookshelf/config.json` |

```json
{
  "quote_cadence": 5,
  "context_matching": true
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `quote_cadence` | 5 | Show a quote every Nth tool call |
| `context_matching` | true | Match quotes to your coding context |

Common cadence values are `5` (default), `10`, or `20`. Flip between them without editing JSON:

```bash
python3 -m bookshelf.skill.cadence              # show current
python3 -m bookshelf.skill.cadence 10           # set Claude cadence to 10
python3 -m bookshelf.skill.cadence 20 --codex   # set Codex cadence to 20
python3 -m bookshelf.skill.cadence 10 --both    # set both to 10
```

### How it works

The hook runs after every tool call. It tracks a counter and shows a quote every `quote_cadence` calls. When `context_matching` is enabled, it reads the tool name, command, and file path to pick a relevant quote:

| Coding Context | Quote Tags |
|---------------|------------|
| Debugging, fixing bugs | perseverance, resilience, patience |
| Building, creating | creativity, ambition, innovation |
| Testing | discipline, focus, perseverance |
| Shipping, deploying | courage, risk, ambition |
| Refactoring | simplicity, growth, change |
| Late night work | solitude, perseverance, focus |

### Troubleshooting

**`ModuleNotFoundError: No module named 'bookshelf'`**
You need to install the package. Run `pip install -e .` from the repo root.

**No quotes appearing**
- Check that the path in `settings.json` points to the actual `hook.py` location
- The hook shows a quote every 5th tool call by default — use a few tools and wait
- Verify Python 3.10+ is your default `python3`

**Quotes aren't matching my context**
- Make sure `context_matching` is `true` in your config file (it is by default)
- Context matching reads the tool name and command — it works best with Bash, Read, and Edit calls

## Codex Ambient Quotes

A `notify` hook for [Codex](https://github.com/openai/codex) that delivers a book quote every 5 turns while you work.

> Codex's `notify` only fires on `turn-ended` (once per assistant response, not per tool call) and does not render the hook's stdout in chat. So the Codex flavor surfaces quotes via macOS notification on every 5th turn. On Linux/Windows the quote is written to Codex's turn log via stderr.

### Quick Start

**Requirements:** Python 3.10+, [Codex](https://github.com/openai/codex), macOS for the notification surface (Linux/Windows fall back to log output)

**Step 1.** Clone and install (skip if you already did this for the Claude hook):

```bash
git clone https://github.com/Amal-David/terminal-arcade.git
cd terminal-arcade
pip install -e .
```

**Step 2.** Open `~/.codex/config.toml` and add the `notify` line at the top level:

```toml
notify = ["python3", "/path/to/terminal-arcade/bookshelf/skill/codex_notify.py"]
```

If you **already have a `notify` line**, Codex only honors one entry — wrap both behind a tiny dispatcher script that calls each in turn, or pick whichever you need most.

**Step 3.** Replace `/path/to/terminal-arcade` with the actual path where you cloned the repo.

**Step 4.** Restart Codex. A book quote will pop as a macOS notification on every 5th turn.

### Configuration

The Codex hook reads the same config file as the Claude hook:

| Platform | Config path |
|----------|-------------|
| macOS | `~/Library/Application Support/bookshelf/config.json` |
| Linux | `~/.local/share/bookshelf/config.json` |
| Windows | `%APPDATA%/bookshelf/config.json` |

```json
{
  "codex_quote_cadence": 5
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `codex_quote_cadence` | 5 | Show a quote every Nth Codex turn |

The Codex counter (`codex_turn_count`) is tracked separately from Claude's tool-call counter, so the two hooks don't interfere if you run both.

### How it works

Codex calls the script with `turn-ended <json_payload>` after every assistant turn. The script ignores all other events, increments its own turn counter, and on every Nth turn picks a quote and surfaces it as a macOS notification (`osascript`). Quote selection reuses the same picker as the Claude hook — recently-shown quotes are deprioritized and the unseen pool is exhausted before repeats.

### Troubleshooting

**`ModuleNotFoundError: No module named 'bookshelf'`**
Run `pip install -e .` from the repo root.

**No notifications appearing**
- Confirm `osascript -e 'display notification "test" with title "test"'` works in your terminal — Notification Center may need permission for your terminal app under System Settings → Notifications.
- The hook fires every 5 turns by default — keep working, it'll show up.
- Check that the path in `~/.codex/config.toml` points to the actual `codex_notify.py` location.

**Notifications appear too often / not often enough**
Bump `codex_quote_cadence`. Cadence counts Codex turns (one per assistant response), not individual tool calls.

## Test

```bash
python3 -m unittest discover -s tests -v
```

## License

[MIT](LICENSE)
