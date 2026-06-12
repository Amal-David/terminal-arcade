#!/usr/bin/env python3
"""PostToolUse hook for Claude Code — shows a language phrase every Nth tool call.

Reads the active language pair from polyglot's config and picks a phrase from
that pair's content (alphabet, vocab, sentences). When the active pair changes,
the picker history resets so variety starts fresh for the new language.

Install via polyglot's TUI installer, or manually add to ~/.claude/settings.json:
{
  "hooks": {
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/terminal-arcade/polyglot/skill/hook.py",
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

from polyglot.skill.phrase_picker import (  # noqa: E402,F401
    RECENT_WINDOW,
    format_phrase_message,
    pick_phrase,
    select_phrase_index,
    total_phrase_count,
)


def main() -> None:
    try:
        json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        pass

    from polyglot.skill.config import (
        get_active_pair_id,
        get_cadence,
        load_hook_state,
        save_hook_state,
    )

    state = load_hook_state()
    call_count = state.get("call_count", 0) + 1
    state["call_count"] = call_count
    save_hook_state(state)

    pair_id = get_active_pair_id()
    if not pair_id:
        print(json.dumps({}))
        return

    cadence = get_cadence()
    if cadence <= 0 or call_count % cadence != 0:
        print(json.dumps({}))
        return

    phrase = pick_phrase(pair_id)
    if not phrase:
        print(json.dumps({}))
        return

    message = format_phrase_message(
        phrase, total_phrase_count(pair_id), phrase["pair_label"]
    )
    print(json.dumps({"systemMessage": message}))


if __name__ == "__main__":
    main()
