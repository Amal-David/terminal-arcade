"""Shared phrase-selection logic used by the Claude and Codex hooks.

Picks a phrase with variety: deprioritizes recently shown phrases and phrases
already shown several times, exhausting the unseen pool before repeating.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

RECENT_WINDOW = 50


def _phrase_score(idx: int, shown_counts: dict[str, int], recent_set: set[int]) -> float:
    score = 0.0
    if idx in recent_set:
        score -= 5.0
    score -= shown_counts.get(str(idx), 0) * 0.5
    return score


def select_phrase_index(
    phrases: list,
    shown_counts: dict[str, int],
    recent_indices: list[int],
) -> int:
    if not phrases:
        raise ValueError("select_phrase_index requires a non-empty phrases list")
    recent_set = set(recent_indices)
    unseen = [i for i in range(len(phrases)) if shown_counts.get(str(i), 0) == 0]

    candidate_indices = [i for i in unseen if i not in recent_set]
    if not candidate_indices:
        candidate_indices = unseen
    if not candidate_indices:
        candidate_indices = [i for i in range(len(phrases)) if i not in recent_set]
    if not candidate_indices:
        candidate_indices = list(range(len(phrases)))

    candidates = [
        (_phrase_score(i, shown_counts, recent_set), i) for i in candidate_indices
    ]
    candidates.sort(key=lambda x: x[0], reverse=True)
    top_score = candidates[0][0]
    top_tier = [(score, idx) for score, idx in candidates if score >= top_score - 1.0]
    _, idx = random.choice(top_tier)
    return idx


def format_phrase_message(phrase: dict, total_phrases: int, pair_label: str) -> str:
    pron = phrase.get("pronunciation", "")
    note = phrase.get("note", "")
    target = phrase.get("target", "")
    source = phrase.get("source", "")
    pron_part = f"  [{pron}]" if pron else ""
    note_part = f"\n   note: {note}" if note else ""
    stats = f"[{phrase['unique_shown']}/{total_phrases} unique phrases shown]"
    return (
        f"🌍 {target}{pron_part}\n"
        f'   — "{source}" ({pair_label})'
        f"{note_part}\n"
        f"   {stats}"
    )


def pick_phrase(pair_id: str | None = None) -> dict | None:
    """Pick a phrase from the active language pair.

    Side effects: updates shown_counts, recent_indices, last_phrase_idx,
    total_phrases_shown, and active_pair_id in the shared hook state. When
    the active pair changes, picker history is reset so variety restarts.
    """
    from polyglot.data.content_loader import get_pair
    from polyglot.skill.config import (
        get_active_pair_id,
        load_hook_state,
        save_hook_state,
    )

    if pair_id is None:
        pair_id = get_active_pair_id()
    if not pair_id:
        return None

    pair = get_pair(pair_id)
    if not pair or not pair.phrases:
        return None

    state = load_hook_state()
    if state.get("active_pair_id") != pair_id:
        state["active_pair_id"] = pair_id
        state["shown_counts"] = {}
        state["recent_indices"] = []
        state["last_phrase_idx"] = -1
        state["total_phrases_shown"] = 0

    shown_counts: dict[str, int] = state.get("shown_counts", {}) or {}
    recent_indices: list[int] = state.get("recent_indices", []) or []
    idx = select_phrase_index(list(pair.phrases), shown_counts, recent_indices)
    entry = pair.phrases[idx]

    shown_counts[str(idx)] = shown_counts.get(str(idx), 0) + 1
    recent_indices.append(idx)
    if len(recent_indices) > RECENT_WINDOW:
        recent_indices = recent_indices[-RECENT_WINDOW:]

    state["shown_counts"] = shown_counts
    state["recent_indices"] = recent_indices
    state["last_phrase_idx"] = idx
    state["total_phrases_shown"] = state.get("total_phrases_shown", 0) + 1
    save_hook_state(state)

    return {
        "source": entry.source,
        "target": entry.target,
        "pronunciation": entry.pronunciation,
        "category": entry.category,
        "subcategory": entry.subcategory,
        "note": entry.note,
        "pair_id": pair.id,
        "pair_label": f"{pair.source_lang} → {pair.target_lang}",
        "times_shown": shown_counts[str(idx)],
        "total_shown": state["total_phrases_shown"],
        "unique_shown": len(shown_counts),
    }


def total_phrase_count(pair_id: str | None = None) -> int:
    from polyglot.data.content_loader import get_pair
    from polyglot.skill.config import get_active_pair_id

    if pair_id is None:
        pair_id = get_active_pair_id()
    if not pair_id:
        return 0
    pair = get_pair(pair_id)
    return len(pair.phrases) if pair else 0
