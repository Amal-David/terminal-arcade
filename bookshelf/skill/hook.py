#!/usr/bin/env python3
"""PostToolUse hook for Claude Code — shows a book quote every Nth tool call.

Tracks which quotes have been shown and how many times, so you get
variety across your session. Quotes are deprioritized after being shown
and only repeat once the full pool is exhausted.

Install by adding to ~/.claude/settings.json:
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
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Re-exported for backward compatibility (anything importing from hook.py keeps working).
from bookshelf.skill.quote_picker import (  # noqa: E402,F401
    RECENT_WINDOW,
    format_quote_message,
    get_context_tags,
    pick_quote,
    select_quote_index,
    total_quote_count,
)


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        input_data = {}

    from bookshelf.skill.config import get_cadence, is_context_matching_enabled, update_hook_state

    def increment_call(state: dict) -> int:
        call_count = state.get("call_count", 0) + 1
        state["call_count"] = call_count
        return call_count

    call_count = update_hook_state(increment_call)

    cadence = get_cadence()

    if call_count % cadence != 0:
        print(json.dumps({}))
        return

    context_tags = None
    if is_context_matching_enabled():
        context_tags = get_context_tags(input_data)

    quote = pick_quote(context_tags)

    if not quote:
        print(json.dumps({}))
        return

    message = format_quote_message(quote, total_quote_count())

    result = {"systemMessage": message}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
