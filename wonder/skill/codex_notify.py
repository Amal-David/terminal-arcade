#!/usr/bin/env python3
"""Codex `notify` hook — surfaces today's Wonder.

Codex invokes notify programs as:

    notify_program <event_name> <json_payload>

Only the ``turn-ended`` event triggers a Wonder. Codex does not render notify
stdout in chat, so on macOS the wonder is surfaced via osascript notification;
on other platforms it is written to stderr (which lands in Codex's turn log).

Default cadence is "daily" — at most one Wonder per local calendar day.
Switch to per-N-turn mode with `python3 -m wonder.skill.cadence 5 --codex`.

Install by adding to ``~/.codex/config.toml``:

    notify = ["python3", "/path/to/terminal-arcade/wonder/skill/codex_notify.py"]
"""

from __future__ import annotations

import datetime as _dt
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _osascript_quote(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def surface_wonder(title: str, body: str) -> None:
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

    sys.stderr.write(f"✨ {title}\n   {body}\n")


def _should_fire(cadence, state: dict) -> bool:
    today = _dt.date.today().isoformat()
    if cadence == "off":
        return False
    if cadence == "daily":
        last = state.get("codex_last_shown_date")
        if last == today:
            return False
        state["codex_last_shown_date"] = today
        return True
    if isinstance(cadence, int) and cadence >= 1:
        count = state.get("codex_turn_count", 0) + 1
        state["codex_turn_count"] = count
        return count % cadence == 0
    return False


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv if argv is None else argv

    event = argv[1] if len(argv) > 1 else ""
    if event != "turn-ended":
        return 0

    from wonder.skill.config import (
        get_codex_cadence,
        load_hook_state,
        save_hook_state,
    )
    from wonder.skill.wonder_picker import format_notification, pick_wonder

    state = load_hook_state()
    cadence = get_codex_cadence()
    fire = _should_fire(cadence, state)
    save_hook_state(state)

    if not fire:
        return 0

    story = pick_wonder()
    if not story or not story.get("body"):
        return 0

    title, body = format_notification(story)
    try:
        surface_wonder(title, body)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit(0)
