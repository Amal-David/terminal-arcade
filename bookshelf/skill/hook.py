#!/usr/bin/env python3
"""PostToolUse hook — shows a book quote every Nth tool call.

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
import random
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# How many recent quote indices to avoid repeating
RECENT_WINDOW = 50


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
    """Pick a quote, avoiding recently shown ones and deprioritizing repeats."""
    from bookshelf.data.quotes import QUOTES
    from bookshelf.skill.config import load_hook_state, save_hook_state

    if not QUOTES:
        return None

    state = load_hook_state()
    shown_counts: dict[str, int] = state.get("shown_counts", {})
    recent_indices: list[int] = state.get("recent_indices", [])
    recent_set = set(recent_indices)

    total = len(QUOTES)

    # Build candidate list with scoring
    candidates: list[tuple[float, int]] = []

    for i, q in enumerate(QUOTES):
        score = 0.0

        # Context relevance (0-3 points)
        if context_tags:
            overlap = len(set(q.tags) & set(context_tags))
            score += overlap

        # Penalize recently shown (strong penalty)
        if i in recent_set:
            score -= 5.0

        # Penalize frequently shown (mild penalty per showing)
        times_shown = shown_counts.get(str(i), 0)
        score -= times_shown * 0.5

        candidates.append((score, i))

    # Sort by score descending, then pick randomly from the top tier
    candidates.sort(key=lambda x: x[0], reverse=True)
    top_score = candidates[0][0]

    # Top tier = anything within 1 point of the best score
    top_tier = [(s, i) for s, i in candidates if s >= top_score - 1.0]

    # Pick randomly from top tier
    _, idx = random.choice(top_tier)
    q = QUOTES[idx]

    # Update state
    shown_counts[str(idx)] = shown_counts.get(str(idx), 0) + 1
    recent_indices.append(idx)
    # Keep recent window bounded
    if len(recent_indices) > RECENT_WINDOW:
        recent_indices = recent_indices[-RECENT_WINDOW:]

    state["shown_counts"] = shown_counts
    state["recent_indices"] = recent_indices
    state["last_quote_idx"] = idx
    state["total_quotes_shown"] = state.get("total_quotes_shown", 0) + 1
    save_hook_state(state)

    times = shown_counts[str(idx)]
    return {
        "text": q.text,
        "author": q.author,
        "book": q.book_title,
        "tags": list(q.tags),
        "times_shown": times,
        "total_shown": state["total_quotes_shown"],
        "unique_shown": len(shown_counts),
    }


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        input_data = {}

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
    stats = f"[{quote['unique_shown']}/485 unique quotes shown]"
    message = f'📖 "{quote["text"]}"\n   — {quote["author"]}, {quote["book"]}\n   {tags_str}\n   {stats}'

    result = {"systemMessage": message}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
