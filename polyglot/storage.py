"""Local persistence for polyglot config, state, and the active language pair."""

from __future__ import annotations

import json
from pathlib import Path

from terminal_arcade.platform import app_data_dir, atomic_write_json

APP_DIR_NAME = "polyglot"
STATE_FILE = "state.json"
CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "active_pair_id": None,
    "phrase_cadence": 5,
    "codex_phrase_cadence": 5,
    "last_browsed_pair_id": None,
}

DEFAULT_STATE = {
    "favorites": [],
    "phrases_seen": 0,
    "pair_history": [],
}


def data_dir(base_dir: Path | None = None) -> Path:
    return app_data_dir(APP_DIR_NAME, base_dir)


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
    atomic_write_json(path, payload)


def load_state(base_dir: Path | None = None) -> dict:
    return _load_json(STATE_FILE, DEFAULT_STATE, base_dir)


def save_state(state: dict, base_dir: Path | None = None) -> None:
    _save_json(STATE_FILE, state, base_dir)


def load_config(base_dir: Path | None = None) -> dict:
    return _load_json(CONFIG_FILE, DEFAULT_CONFIG, base_dir)


def save_config(config: dict, base_dir: Path | None = None) -> None:
    _save_json(CONFIG_FILE, config, base_dir)


def get_active_pair_id(base_dir: Path | None = None) -> str | None:
    config = load_config(base_dir)
    pair_id = config.get("active_pair_id")
    return pair_id if pair_id else None


def set_active_pair_id(pair_id: str | None, base_dir: Path | None = None) -> None:
    config = load_config(base_dir)
    config["active_pair_id"] = pair_id
    if pair_id:
        history = list(config.get("pair_history", []) if isinstance(config.get("pair_history"), list) else [])
        if pair_id in history:
            history.remove(pair_id)
        history.append(pair_id)
        config["pair_history"] = history[-20:]
        config["last_browsed_pair_id"] = pair_id
    save_config(config, base_dir)


def increment_phrases_seen(base_dir: Path | None = None) -> None:
    state = load_state(base_dir)
    state["phrases_seen"] = state.get("phrases_seen", 0) + 1
    save_state(state, base_dir)
