"""Local persistence for bookshelf state and config."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

APP_DIR_NAME = "bookshelf"
STATE_FILE = "state.json"
CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "quote_cadence": 5,
    "context_matching": True,
    "preferred_genres": ["motivation", "startup", "romance"],
}

DEFAULT_STATE = {
    "favorites": [],
    "read": [],
    "want_to_read": [],
    "last_viewed_book": None,
    "quotes_seen": 0,
    "books_explored": 0,
}


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


def _load_json(filename: str, defaults: dict, base_dir: Path | None = None) -> dict:
    path = data_dir(base_dir) / filename
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return dict(defaults)
        merged = dict(defaults)
        merged.update(payload)
        return merged
    except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError, ValueError):
        return dict(defaults)


def _save_json(filename: str, payload: dict, base_dir: Path | None = None) -> None:
    path = data_dir(base_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_state(base_dir: Path | None = None) -> dict:
    return _load_json(STATE_FILE, DEFAULT_STATE, base_dir)


def save_state(state: dict, base_dir: Path | None = None) -> None:
    _save_json(STATE_FILE, state, base_dir)


def load_config(base_dir: Path | None = None) -> dict:
    return _load_json(CONFIG_FILE, DEFAULT_CONFIG, base_dir)


def save_config(config: dict, base_dir: Path | None = None) -> None:
    _save_json(CONFIG_FILE, config, base_dir)


def toggle_favorite(title: str, base_dir: Path | None = None) -> bool:
    """Toggle a book in favorites. Returns True if added, False if removed."""
    state = load_state(base_dir)
    if title in state["favorites"]:
        state["favorites"].remove(title)
        added = False
    else:
        state["favorites"].append(title)
        added = True
    save_state(state, base_dir)
    return added


def mark_read(title: str, base_dir: Path | None = None) -> None:
    state = load_state(base_dir)
    if title not in state["read"]:
        state["read"].append(title)
    if title in state["want_to_read"]:
        state["want_to_read"].remove(title)
    save_state(state, base_dir)


def mark_want_to_read(title: str, base_dir: Path | None = None) -> None:
    state = load_state(base_dir)
    if title not in state["want_to_read"]:
        state["want_to_read"].append(title)
    save_state(state, base_dir)


def increment_stats(
    books_explored: int = 0, quotes_seen: int = 0, base_dir: Path | None = None
) -> None:
    state = load_state(base_dir)
    state["books_explored"] = state.get("books_explored", 0) + books_explored
    state["quotes_seen"] = state.get("quotes_seen", 0) + quotes_seen
    save_state(state, base_dir)
