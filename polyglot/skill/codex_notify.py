#!/usr/bin/env python3
"""Codex `notify` hook — fires a language phrase every Nth turn-ended event.

Codex invokes notify programs as:

    notify_program <event_name> <json_payload>

Only the ``turn-ended`` event triggers a phrase. Codex does not render notify
stdout in chat, so on macOS the phrase is surfaced via osascript notification;
on other platforms it is written to stderr (which lands in Codex's turn log).

Install via polyglot's TUI installer, or manually add to ``~/.codex/config.toml``:

    notify = ["python3", "/path/to/terminal-arcade/polyglot/skill/codex_notify.py"]
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


NOTIFICATION_BODY_MAX = 200


def _truncate(text: str, limit: int = NOTIFICATION_BODY_MAX) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _osascript_quote(s: str) -> str:
    """Escape a string for safe embedding inside an AppleScript double-quoted literal.

    Backslash first (so we don't double-escape the escapes we add next), then
    quotes, then any control characters that would let phrase text break out
    of the string literal (newlines, carriage returns, tabs).
    """
    return (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def surface_phrase(phrase: dict) -> None:
    target = phrase.get("target", "")
    source = phrase.get("source", "")
    pron = phrase.get("pronunciation", "")
    pair_label = phrase.get("pair_label", "")

    title = f"{pair_label}: {target}"
    body_parts = [f'"{source}"']
    if pron:
        body_parts.append(f"[{pron}]")
    body = _truncate(" ".join(body_parts))

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

    sys.stderr.write(f'🌍 {target}  [{pron}]\n   — "{source}" ({pair_label})\n')


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv if argv is None else argv

    event = argv[1] if len(argv) > 1 else ""
    if event != "turn-ended":
        return 0

    from polyglot.skill.config import (
        get_active_pair_id,
        get_codex_cadence,
        load_hook_state,
        save_hook_state,
    )
    from polyglot.skill.phrase_picker import pick_phrase

    pair_id = get_active_pair_id()
    if not pair_id:
        return 0

    state = load_hook_state()
    turn_count = state.get("codex_turn_count", 0) + 1
    state["codex_turn_count"] = turn_count
    save_hook_state(state)

    cadence = get_codex_cadence()
    if cadence <= 0 or turn_count % cadence != 0:
        return 0

    phrase = pick_phrase(pair_id)
    if not phrase:
        return 0

    try:
        surface_phrase(phrase)
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit(0)
