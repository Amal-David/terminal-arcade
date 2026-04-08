#!/usr/bin/env python3
"""PostToolUse hook — shows a book quote every Nth tool call.

This script reads JSON from stdin (tool call details) and outputs
JSON to stdout with a systemMessage containing a relevant quote.

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
import random
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def get_context_tags(input_data: dict) -> list[str]:
    """Extract context tags from tool call data."""
    from bookshelf.data.categories import CONTEXT_MAP

    text_sources = []

    tool_name = input_data.get("tool_name", "")
    text_sources.append(tool_name.lower())

    command = input_data.get("command", "")
    if command:
        text_sources.append(command.lower())

    file_path = input_data.get("file_path", "")
    if file_path:
        text_sources.append(file_path.lower())

    combined = " ".join(text_sources)

    matched_tags = set()
    for keyword, tags in CONTEXT_MAP.items():
        if keyword in combined:
            matched_tags.update(tags)

    return list(matched_tags)


def pick_quote(context_tags: list[str] | None = None) -> dict | None:
    """Pick a quote, optionally matching context tags."""
    from bookshelf.data.quotes import QUOTES
    from bookshelf.skill.config import load_hook_state, save_hook_state

    if not QUOTES:
        return None

    state = load_hook_state()
    last_idx = state.get("last_quote_idx", -1)

    if context_tags:
        # Score quotes by tag overlap
        scored = []
        for i, q in enumerate(QUOTES):
            overlap = len(set(q.tags) & set(context_tags))
            if overlap > 0:
                scored.append((overlap, i, q))

        if scored:
            # Pick from top-scoring quotes, avoiding the last shown
            scored.sort(key=lambda x: x[0], reverse=True)
            top_score = scored[0][0]
            candidates = [(i, q) for s, i, q in scored if s >= top_score - 1 and i != last_idx]

            if candidates:
                idx, quote = random.choice(candidates)
                state["last_quote_idx"] = idx
                save_hook_state(state)
                return {"text": quote.text, "author": quote.author, "book": quote.book_title, "tags": list(quote.tags)}

    # Fallback: random quote
    available = [i for i in range(len(QUOTES)) if i != last_idx]
    if not available:
        available = list(range(len(QUOTES)))

    idx = random.choice(available)
    q = QUOTES[idx]
    state["last_quote_idx"] = idx
    save_hook_state(state)
    return {"text": q.text, "author": q.author, "book": q.book_title, "tags": list(q.tags)}


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        input_data = {}

    # Load state and check cadence
    from bookshelf.skill.config import load_hook_state, save_hook_state, get_cadence, is_context_matching_enabled

    state = load_hook_state()
    call_count = state.get("call_count", 0) + 1
    state["call_count"] = call_count
    save_hook_state(state)

    cadence = get_cadence()

    # Only show a quote every Nth call
    if call_count % cadence != 0:
        print(json.dumps({}))
        return

    # Pick a quote
    context_tags = None
    if is_context_matching_enabled():
        context_tags = get_context_tags(input_data)

    quote = pick_quote(context_tags)

    if not quote:
        print(json.dumps({}))
        return

    # Format the quote as a system message
    tags_str = " ".join(f"#{t}" for t in quote["tags"][:3])
    message = f'📖 "{quote["text"]}"\n   — {quote["author"]}, {quote["book"]}\n   {tags_str}'

    result = {"systemMessage": message}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
