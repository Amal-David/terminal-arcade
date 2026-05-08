#!/usr/bin/env python3
"""Codex `notify` hook — fires a book quote every Nth turn-ended event.

Codex invokes notify programs as:

    notify_program <event_name> <json_payload>

Only the ``turn-ended`` event triggers a quote. Codex does not render
notify stdout in chat, so on macOS the quote is surfaced via osascript
notification; on other platforms it is written to stderr (which lands
in Codex's turn log).

Install by adding to ``~/.codex/config.toml``:

    notify = ["python3", "/path/to/terminal-arcade/bookshelf/skill/codex_notify.py"]
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# macOS notification body has a hard cap; longer strings get truncated by
# Notification Center anyway, so trim with an ellipsis to keep the meaning.
NOTIFICATION_BODY_MAX = 200


def _truncate(text: str, limit: int = NOTIFICATION_BODY_MAX) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _osascript_quote(s: str) -> str:
    """Quote a string for embedding inside an AppleScript double-quoted literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def surface_quote(quote: dict) -> None:
    """Display the quote to the user. macOS gets a notification; other
    platforms get a stderr line."""
    title = f"{quote['book']} — {quote['author']}"
    body = _truncate(quote["text"])

    if sys.platform == "darwin":
        script = (
            f'display notification "{_osascript_quote(body)}" '
            f'with title "{_osascript_quote(title)}" '
            f'sound name "Glass"'
        )
        try:
            subprocess.run(
                ["osascript", "-e", script],
                check=False,
                capture_output=True,
                timeout=3,
            )
            return
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass

    sys.stderr.write(f'📖 "{quote["text"]}"\n   — {quote["author"]}, {quote["book"]}\n')


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv if argv is None else argv

    event = argv[1] if len(argv) > 1 else ""
    if event != "turn-ended":
        return 0

    from bookshelf.skill.config import get_codex_cadence, load_hook_state, save_hook_state
    from bookshelf.skill.quote_picker import pick_quote

    state = load_hook_state()
    turn_count = state.get("codex_turn_count", 0) + 1
    state["codex_turn_count"] = turn_count
    save_hook_state(state)

    cadence = get_codex_cadence()
    if cadence <= 0 or turn_count % cadence != 0:
        return 0

    quote = pick_quote()
    if not quote:
        return 0

    try:
        surface_quote(quote)
    except Exception:
        # Never let a notification failure break Codex's turn pipeline.
        pass

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        # Defensive: never propagate. Codex calls notify fire-and-forget.
        raise SystemExit(0)
