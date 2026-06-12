"""Fetch a daily Story per category, with internet-first + offline fallback.

The fetcher exposes one main entry point — `fetch_story(category, force_refresh)` —
that consults the on-disk cache, then the network, and finally a bundled set
of curated fallbacks. The fallback path never writes to the cache, so a future
online open can still bring fresh content.
"""

from __future__ import annotations

import datetime as _dt
import json
import random
import socket
import urllib.error
import urllib.request
from typing import Iterable

from wonder.data.fallback import FALLBACKS
from wonder.storage import load_cache, save_cache

USER_AGENT = "terminal-arcade-wonder/0.1 (+https://github.com/amaldavid/terminal-arcade)"
DEFAULT_TIMEOUT = 5

CATEGORIES = ["funny", "heartwarming", "weird", "inspiring"]
SURPRISE = "surprise"

CATEGORY_LABELS = {
    "funny": "Funny",
    "heartwarming": "Heartwarming",
    "weird": "Weird Facts",
    "inspiring": "Inspiring",
    SURPRISE: "Surprise me",
}

CATEGORY_ICONS = {
    "funny": "😄",
    "heartwarming": "💛",
    "weird": "🤯",
    "inspiring": "✨",
    SURPRISE: "🎲",
}


def _today() -> str:
    return _dt.date.today().isoformat()


def _build_request(url: str, accept: str = "application/json") -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
        },
    )


def _fetch_json(url: str, timeout: int) -> dict | list:
    req = _build_request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def _story(category: str, title: str, body: str, source: str, url: str | None, origin: str) -> dict:
    return {
        "category": category,
        "title": (title or "").strip(),
        "body": (body or "").strip(),
        "source": source,
        "url": url,
        "fetched_at": _today(),
        "origin": origin,
    }


def _pick_reddit_post(payload, seen_titles: Iterable[str] = ()) -> dict | None:
    children = payload.get("data", {}).get("children", []) if isinstance(payload, dict) else []
    skipped = set(seen_titles)
    fallback = None
    for child in children:
        post = child.get("data", {}) if isinstance(child, dict) else {}
        title = (post.get("title") or "").strip()
        if not title:
            continue
        if fallback is None:
            fallback = post
        if post.get("stickied"):
            continue
        if title in skipped:
            continue
        return post
    return fallback


def _from_dadjoke(timeout: int) -> dict:
    payload = _fetch_json("https://icanhazdadjoke.com/", timeout)
    body = payload.get("joke", "") if isinstance(payload, dict) else ""
    if not body:
        raise ValueError("empty dad joke")
    return _story("funny", "Dad joke", body, "icanhazdadjoke.com", "https://icanhazdadjoke.com/", "live")


def _from_uselessfacts(timeout: int) -> dict:
    payload = _fetch_json(
        "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en", timeout
    )
    body = payload.get("text", "") if isinstance(payload, dict) else ""
    src_url = payload.get("source_url") if isinstance(payload, dict) else None
    if not body:
        raise ValueError("empty fact")
    return _story("weird", "Did you know?", body, "uselessfacts.jsph.pl", src_url, "live")


def _from_subreddit(category: str, subreddit: str, label: str, timeout: int, exclude_titles: list[str]) -> dict:
    url = f"https://www.reddit.com/r/{subreddit}/top.json?t=day&limit=15"
    payload = _fetch_json(url, timeout)
    post = _pick_reddit_post(payload, exclude_titles)
    if not post:
        raise ValueError("no reddit posts found")
    title = (post.get("title") or "").strip()
    body = (post.get("selftext") or "").strip()
    permalink = post.get("permalink")
    full_url = f"https://www.reddit.com{permalink}" if permalink else post.get("url")
    if not body:
        body = f"From r/{subreddit}. Read the full story at the link below."
    return _story(category, title, body, label, full_url, "live")


def _fallback_story(category: str, seed_extra: str = "") -> dict:
    bundle = FALLBACKS.get(category) or []
    if not bundle:
        return _story(category, "Wonder", "No fallback available.", "Bundled", None, "fallback")
    seed = f"{_today()}|{category}|{seed_extra}"
    rng = random.Random(seed)
    pick = rng.choice(bundle)
    return _story(
        category,
        pick.get("title", "Wonder"),
        pick.get("body", ""),
        pick.get("source", "Bundled"),
        None,
        "fallback",
    )


def _try_fetch(category: str, timeout: int, exclude_titles: list[str] | None = None) -> dict:
    excludes = exclude_titles or []
    if category == "funny":
        return _from_dadjoke(timeout)
    if category == "weird":
        return _from_uselessfacts(timeout)
    if category == "heartwarming":
        return _from_subreddit("heartwarming", "UpliftingNews", "r/UpliftingNews", timeout, excludes)
    if category == "inspiring":
        return _from_subreddit("inspiring", "MadeMeSmile", "r/MadeMeSmile", timeout, excludes)
    raise ValueError(f"unknown category: {category}")


def fetch_story(category: str, *, force_refresh: bool = False, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Return a Story dict for `category`, using cache → network → fallback."""
    if category == SURPRISE:
        seed = f"{_today()}|surprise"
        pick = random.Random(seed).choice(CATEGORIES)
        story = fetch_story(pick, force_refresh=force_refresh, timeout=timeout)
        return story

    today = _today()
    cache = load_cache()
    day = cache.get(today, {})

    if not force_refresh and category in day:
        cached = dict(day[category])
        cached["origin"] = "cache"
        return cached

    exclude_titles: list[str] = []
    if force_refresh and category in day:
        prev = day[category]
        if isinstance(prev, dict) and prev.get("title"):
            exclude_titles.append(prev["title"])

    try:
        story = _try_fetch(category, timeout, exclude_titles)
    except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout, json.JSONDecodeError, ValueError, OSError, TimeoutError):
        return _fallback_story(category, seed_extra="refresh" if force_refresh else "")

    cache.setdefault(today, {})[category] = story
    try:
        save_cache(cache)
    except OSError:
        pass
    return story
