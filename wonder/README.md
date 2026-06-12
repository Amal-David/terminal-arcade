# Wonder

Pick a mood — funny, heartwarming, weird, or inspiring — and pull one fresh fact or story from the internet for the day. Caches the day's pick so re-opens are instant, falls back to a bundled curated set when offline, and lets you save anything that landed for later. Zero external dependencies — uses stdlib `urllib` and free public APIs (icanhazdadjoke, uselessfacts, r/UpliftingNews, r/MadeMeSmile).

## Run

```bash
python3 -m wonder    # or: wonder
```

## Controls

| Key | Action |
|-----|--------|
| `↑` / `↓` or `j` / `k` | Navigate moods |
| `Enter` | Pull today's wonder for this mood |
| `R` | Force-refresh (fetch new content mid-day) |
| `s` | Save the current wonder to favorites |
| `v` | View saved wonders |
| `q` / `Esc` | Quit |

## Ambient Hook — Claude Code

The Wonder cabinet doubles as an ambient hook. Once a day (by default) you'll get one fresh fact or story surfaced inline while you work. The hook never touches the network directly — it reads whatever the Wonder app has cached for today, or falls back to a bundled curated pick if nothing's cached yet. Open the cabinet (`python3 -m wonder`) any time to pre-warm the next pick.

**Requirements:** Python 3.10+, Claude Code, `pip install -e .` already run

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/terminal-arcade/wonder/skill/hook.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Replace `/path/to/terminal-arcade` with the real path. Restart Claude Code. The first tool call each day surfaces a Wonder via `systemMessage`; subsequent calls that day are silent.

## Ambient Hook — Codex

Add the notify line to `~/.codex/config.toml`:

```toml
notify = ["python3", "/path/to/terminal-arcade/wonder/skill/codex_notify.py"]
```

On macOS the wonder pops as a Notification Center alert on the first turn each day; other platforms get a stderr line in the turn log.

## Cadence

`daily` is the default. Switch with the CLI:

```bash
python3 -m wonder.skill.cadence                  # show current
python3 -m wonder.skill.cadence daily            # Claude: once per day (default)
python3 -m wonder.skill.cadence 5                # Claude: every 5th tool call
python3 -m wonder.skill.cadence off              # Claude: disable
python3 -m wonder.skill.cadence 10 --codex       # Codex: every 10th turn
python3 -m wonder.skill.cadence daily --both     # both: once per day
```

Pin a mood instead of rotating daily:

```bash
python3 -m wonder.skill.cadence --category funny
python3 -m wonder.skill.cadence --category rotate    # back to daily rotation
```

| Setting | Default | Description |
|---------|---------|-------------|
| `wonder_cadence` | `daily` | Claude hook: `daily` / `<int>` / `off` |
| `codex_wonder_cadence` | `daily` | Codex hook: `daily` / `<int>` / `off` |
| `wonder_category` | `rotate` | `rotate`, `funny`, `heartwarming`, `weird`, `inspiring`, `surprise` |

Config lives alongside the Wonder app data — e.g. `~/Library/Application Support/wonder/` on macOS.

## Troubleshooting

**`ModuleNotFoundError: No module named 'wonder'`** — run `pip install -e .` from the repo root.

**Always shows the same offline pick** — open the Wonder cabinet at least once so it can fetch live content: `python3 -m wonder`. Until then the hook surfaces the deterministic bundled fallback.

**Want a fresh pick mid-day** — inside the cabinet press `R` to force-refresh the current category. The hook picks up the new cached entry on its next fire.

## License

[MIT](../LICENSE)
