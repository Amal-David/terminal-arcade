#!/usr/bin/env python3
"""PostToolUse hook for Claude Code — surfaces today's Wonder.

Default cadence is "daily" — at most one Wonder per local calendar day,
shown on the first tool call where the hook fires. Switch to per-N-tool-call
mode by running `python3 -m wonder.skill.cadence 5` (matches the bookshelf
cadence model). Turn it off entirely with `python3 -m wonder.skill.cadence off`.

The hook never touches the network. It reads today's pick from the on-disk
cache written by the Wonder app; if no cache exists yet, it surfaces a
deterministic offline pick from the bundled fallback set. This keeps the
Claude tool-call pipeline fast.

Install by adding to `~/.claude/settings.json`:

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
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from wonder.skill.config import (  # noqa: E402
    get_cadence,
    load_hook_state,
    save_hook_state,
)
from wonder.skill.wonder_picker import (  # noqa: E402
    format_system_message,
    pick_wonder,
)


def _should_fire(cadence, state: dict) -> bool:
    """Decide whether to surface a Wonder on this call.

    Mutates `state` with the updated call counter / last-shown date.
    """
    today = _dt.date.today().isoformat()
    if cadence == "off":
        return False
    if cadence == "daily":
        last = state.get("last_shown_date")
        if last == today:
            return False
        state["last_shown_date"] = today
        return True
    if isinstance(cadence, int) and cadence >= 1:
        count = state.get("call_count", 0) + 1
        state["call_count"] = count
        return count % cadence == 0
    return False


def main() -> None:
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        input_data = {}
    # input_data is read for symmetry with bookshelf and future context use.
    _ = input_data

    state = load_hook_state()
    cadence = get_cadence()

    fire = _should_fire(cadence, state)
    save_hook_state(state)

    if not fire:
        print(json.dumps({}))
        return

    story = pick_wonder()
    if not story or not story.get("body"):
        print(json.dumps({}))
        return

    message = format_system_message(story)
    print(json.dumps({"systemMessage": message}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never break the tool-call pipeline.
        print(json.dumps({}))
