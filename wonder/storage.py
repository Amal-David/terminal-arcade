"""Local persistence for wonder state, config, and daily cache."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

APP_DIR_NAME = "wonder"
STATE_FILE = "state.json"
CONFIG_FILE = "config.json"
CACHE_FILE = "cache.json"

DEFAULT_CONFIG = {
    "fetch_timeout": 5,
    "last_category": None,
}

DEFAULT_STATE = {
    "favorites": [],
    "stories_seen": 0,
}

DEFAULT_CACHE: dict = {}


def data_dir(base_dir: Path | None = None) -> Path:
    if base_dir is not None:
        return Path(base_dir)
    home = Path.home()
    if sys.platform == "darwin":
        root = home / "Library" / "Application Support"
    elif os.name == "nt":
        root = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
    return root / APP_DIR_NAME


def _load_json(filename: str, defaults, base_dir: Path | None = None):
    path = data_dir(base_dir) / filename
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError, ValueError):
        return _copy_defaults(defaults)
    if isinstance(defaults, dict):
        if not isinstance(payload, dict):
            return _copy_defaults(defaults)
        merged = dict(defaults)
        merged.update(payload)
        return merged
    return payload


def _copy_defaults(defaults):
    if isinstance(defaults, dict):
        return dict(defaults)
    if isinstance(defaults, list):
        return list(defaults)
    return defaults


def _save_json(filename: str, payload, base_dir: Path | None = None) -> None:
    path = data_dir(base_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_state(base_dir: Path | None = None) -> dict:
    return _load_json(STATE_FILE, DEFAULT_STATE, base_dir)


def save_state(state: dict, base_dir: Path | None = None) -> None:
    _save_json(STATE_FILE, state, base_dir)


def load_config(base_dir: Path | None = None) -> dict:
    return _load_json(CONFIG_FILE, DEFAULT_CONFIG, base_dir)


def save_config(config: dict, base_dir: Path | None = None) -> None:
    _save_json(CONFIG_FILE, config, base_dir)


def load_cache(base_dir: Path | None = None) -> dict:
    return _load_json(CACHE_FILE, DEFAULT_CACHE, base_dir)


def save_cache(cache: dict, base_dir: Path | None = None) -> None:
    _save_json(CACHE_FILE, cache, base_dir)


def is_favorite(story: dict, favorites: list[dict]) -> bool:
    key = (story.get("category"), story.get("title"), story.get("body"))
    for fav in favorites:
        if (fav.get("category"), fav.get("title"), fav.get("body")) == key:
            return True
    return False


def toggle_favorite(story: dict, base_dir: Path | None = None) -> bool:
    """Toggle a story in favorites. Returns True if added, False if removed."""
    state = load_state(base_dir)
    favorites = list(state.get("favorites", []))
    key = (story.get("category"), story.get("title"), story.get("body"))
    matches = [
        fav for fav in favorites
        if (fav.get("category"), fav.get("title"), fav.get("body")) == key
    ]
    if matches:
        for fav in matches:
            favorites.remove(fav)
        added = False
    else:
        favorites.append(dict(story))
        added = True
    state["favorites"] = favorites
    save_state(state, base_dir)
    return added


def remove_favorite_at(index: int, base_dir: Path | None = None) -> None:
    state = load_state(base_dir)
    favorites = list(state.get("favorites", []))
    if 0 <= index < len(favorites):
        favorites.pop(index)
        state["favorites"] = favorites
        save_state(state, base_dir)


def increment_stories_seen(base_dir: Path | None = None) -> None:
    state = load_state(base_dir)
    state["stories_seen"] = state.get("stories_seen", 0) + 1
    save_state(state, base_dir)
