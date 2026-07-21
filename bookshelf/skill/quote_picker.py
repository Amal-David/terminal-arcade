"""Shared quote selection logic used by Claude (hook.py) and Codex (codex_notify.py).

Picks a quote with variety: deprioritizes recently shown quotes and quotes
already shown several times, exhausting the unseen pool before repeating.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# How many recent quote indices to avoid repeating
RECENT_WINDOW = 50


def get_context_tags(input_data: dict) -> list[str]:
    """Extract context tags from tool call data (Claude PostToolUse payload)."""
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


def total_quote_count() -> int:
    """Return the current size of the merged quote catalog."""
    from bookshelf.data.quotes import QUOTES

    return len(QUOTES)


def _quote_score(
    quote,
    idx: int,
    shown_counts: dict[str, int],
    recent_set: set[int],
    context_tags: list[str] | None,
) -> float:
    score = 0.0

    if context_tags:
        score += len(set(quote.tags) & set(context_tags))

    if idx in recent_set:
        score -= 5.0

    score -= shown_counts.get(str(idx), 0) * 0.5
    return score


def select_quote_index(
    quotes: list,
    shown_counts: dict[str, int],
    recent_indices: list[int],
    context_tags: list[str] | None = None,
) -> int:
    """Select a quote index, exhausting unseen quotes before repeating."""
    recent_set = set(recent_indices)
    unseen = [i for i in range(len(quotes)) if shown_counts.get(str(i), 0) == 0]

    candidate_indices = [i for i in unseen if i not in recent_set]
    if not candidate_indices:
        candidate_indices = unseen
    if not candidate_indices:
        candidate_indices = [i for i in range(len(quotes)) if i not in recent_set]
    if not candidate_indices:
        candidate_indices = list(range(len(quotes)))

    candidates = [
        (_quote_score(quotes[i], i, shown_counts, recent_set, context_tags), i)
        for i in candidate_indices
    ]
    candidates.sort(key=lambda x: x[0], reverse=True)
    top_score = candidates[0][0]
    top_tier = [(score, idx) for score, idx in candidates if score >= top_score - 1.0]
    _, idx = random.choice(top_tier)
    return idx


def format_quote_message(quote: dict, total_quotes: int) -> str:
    """Format the quote payload as a Claude-style system message."""
    tags_str = " ".join(f"#{t}" for t in quote["tags"][:3])
    stats = f"[{quote['unique_shown']}/{total_quotes} unique quotes shown]"
    return f'📖 "{quote["text"]}"\n   — {quote["author"]}, {quote["book"]}\n   {tags_str}\n   {stats}'


def pick_quote(context_tags: list[str] | None = None) -> dict | None:
    """Pick a quote, avoiding recently shown ones and deprioritizing repeats.

    Side effects: updates shown_counts, recent_indices, last_quote_idx,
    total_quotes_shown in the shared hook state.
    """
    from bookshelf.data.quotes import QUOTES
    from bookshelf.skill.config import update_hook_state

    if not QUOTES:
        return None

    def choose(state: dict) -> dict:
        shown_counts: dict[str, int] = state.get("shown_counts", {}) or {}
        recent_indices: list[int] = state.get("recent_indices", []) or []
        idx = select_quote_index(QUOTES, shown_counts, recent_indices, context_tags)
        q = QUOTES[idx]

        shown_counts[str(idx)] = shown_counts.get(str(idx), 0) + 1
        recent_indices.append(idx)
        if len(recent_indices) > RECENT_WINDOW:
            recent_indices = recent_indices[-RECENT_WINDOW:]

        state["shown_counts"] = shown_counts
        state["recent_indices"] = recent_indices
        state["last_quote_idx"] = idx
        state["total_quotes_shown"] = state.get("total_quotes_shown", 0) + 1

        return {
            "text": q.text,
            "author": q.author,
            "book": q.book_title,
            "tags": list(q.tags),
            "times_shown": shown_counts[str(idx)],
            "total_shown": state["total_quotes_shown"],
            "unique_shown": len(shown_counts),
        }

    return update_hook_state(choose)
