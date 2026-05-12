"""Pick today's wonder for the ambient hooks.

The picker is non-blocking and never reaches the network. It consults:

1. The on-disk daily cache written by the Wonder app — if today's entry for
   the chosen category exists, use it (origin=cache).
2. The bundled offline fallback set seeded by (date, category) — if no cache
   exists yet, this surfaces a deterministic bundled item.

This keeps PostToolUse / turn-ended hooks predictable and fast (no urllib
calls inside Claude or Codex's hook path).
"""

from __future__ import annotations

import datetime as _dt
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from wonder.data.fallback import FALLBACKS  # noqa: E402
from wonder.fetcher import CATEGORIES, CATEGORY_LABELS, SURPRISE  # noqa: E402
from wonder.skill.config import get_category_preference  # noqa: E402
from wonder.storage import load_cache  # noqa: E402

NOTIFY_BODY_MAX = 200
SYSTEM_MESSAGE_BODY_MAX = 500


def _today() -> str:
    return _dt.date.today().isoformat()


def today_category() -> str:
    """Pick the category for today based on user preference (or rotation)."""
    preference = get_category_preference()
    if preference in CATEGORIES:
        return preference
    if preference == "surprise":
        seed = f"{_today()}|surprise"
        return random.Random(seed).choice(CATEGORIES)
    # default: rotate
    ord_day = _dt.date.today().toordinal()
    return CATEGORIES[ord_day % len(CATEGORIES)]


def _from_cache(category: str) -> dict | None:
    cache = load_cache()
    today = cache.get(_today(), {}) if isinstance(cache, dict) else {}
    story = today.get(category)
    if isinstance(story, dict) and story.get("body"):
        out = dict(story)
        out["origin"] = "cache"
        return out
    return None


def _from_fallback(category: str) -> dict:
    bundle = FALLBACKS.get(category) or []
    if not bundle:
        return {
            "category": category,
            "title": "Wonder",
            "body": "Open Wonder from the arcade to fetch today's pick.",
            "source": "Bundled",
            "url": None,
            "fetched_at": _today(),
            "origin": "fallback",
        }
    seed = f"{_today()}|{category}|skill"
    pick = random.Random(seed).choice(bundle)
    return {
        "category": category,
        "title": pick.get("title", "Wonder"),
        "body": pick.get("body", ""),
        "source": pick.get("source", "Bundled"),
        "url": None,
        "fetched_at": _today(),
        "origin": "fallback",
    }


def pick_wonder(category: str | None = None) -> dict:
    """Return today's wonder for `category` (defaulting to user preference)."""
    cat = category or today_category()
    if cat == SURPRISE:
        seed = f"{_today()}|surprise|skill"
        cat = random.Random(seed).choice(CATEGORIES)
    cached = _from_cache(cat)
    if cached is not None:
        return cached
    return _from_fallback(cat)


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def format_system_message(story: dict) -> str:
    """Format a Wonder for the Claude Code systemMessage surface."""
    category = story.get("category", "")
    label = CATEGORY_LABELS.get(category, category.title() or "Wonder")
    title = (story.get("title") or "").strip()
    body = _truncate((story.get("body") or "").strip(), SYSTEM_MESSAGE_BODY_MAX)
    source = (story.get("source") or "").strip()
    origin = story.get("origin", "")

    header = f"✨ Today's Wonder · {label}"
    if title and title.lower() not in {"dad joke", "did you know?"}:
        header = f"{header} — {title}"
    elif title:
        header = f"{header} ({title})"

    footer_bits = []
    if source:
        footer_bits.append(source)
    if origin == "fallback":
        footer_bits.append("offline pick")
    elif origin == "cache":
        footer_bits.append("today's saved pick")
    footer = " · ".join(footer_bits)
    if footer:
        return f"{header}\n{body}\n— {footer}"
    return f"{header}\n{body}"


def format_notification(story: dict) -> tuple[str, str]:
    """Return (title, body) tuned for a macOS notification."""
    category = story.get("category", "")
    label = CATEGORY_LABELS.get(category, category.title() or "Wonder")
    story_title = (story.get("title") or "").strip()

    if story_title and story_title.lower() not in {"dad joke", "did you know?"}:
        title = f"✨ {label} — {story_title}"
    else:
        title = f"✨ Today's Wonder · {label}"

    body = _truncate((story.get("body") or "").strip(), NOTIFY_BODY_MAX)
    return title, body
