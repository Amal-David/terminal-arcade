# Chess

Terminal chess for the arcade launcher with a built-in rule-based engine and three difficulty levels.

## Run

```bash
# From the repo root
python3 -m chess_game

# Or install and run anywhere
pip install -e .
chess-game
```

## Controls

| Key / Command | Action |
|---|---|
| `Left` / `Right` on title | Change difficulty |
| `1` / `2` / `3` on title | Select Easy / Medium / Hard |
| `Enter` | Start a game |
| `e2e4` | Play a move in UCI form |
| `e7e8q` | Promote to a queen |
| `undo` | Undo the last full turn |
| `new` | Start over |
| `resign` | Concede |
| `q` | Quit |

## Notes

- You always play White in v1.
- The engine is local and rule-based; no network or AI API calls are required.
- Stats are stored locally per difficulty level.

## License

[MIT](../LICENSE)
