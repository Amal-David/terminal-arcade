"""Configuration accessors for the polyglot ambient hooks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from terminal_arcade.platform import app_data_dir, atomic_write_json, locked_json_update

APP_DIR_NAME = "polyglot"

DEFAULT_CADENCE = 5
DEFAULT_CODEX_CADENCE = 5


def _state_dir() -> Path:
    return app_data_dir(APP_DIR_NAME)


HOOK_STATE_FILE = _state_dir() / "hook_state.json"

DEFAULT_HOOK_STATE = {
    "call_count": 0,
    "codex_turn_count": 0,
    "last_phrase_idx": -1,
    "shown_counts": {},
    "recent_indices": [],
    "active_pair_id": None,
    "total_phrases_shown": 0,
}


def load_hook_state() -> dict:
    try:
        return json.loads(HOOK_STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return dict(DEFAULT_HOOK_STATE)


def save_hook_state(state: dict) -> None:
    try:
        atomic_write_json(HOOK_STATE_FILE, state, indent=None)
    except OSError:
        pass


def update_hook_state(update):
    """Run a hook-state read/modify/write transaction under an exclusive lock."""
    return locked_json_update(HOOK_STATE_FILE, DEFAULT_HOOK_STATE, update, indent=None)


def _load_polyglot_config() -> dict:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from polyglot.storage import load_config
        return load_config()
    except Exception:
        return {}


def get_cadence() -> int:
    config = _load_polyglot_config()
    return int(config.get("phrase_cadence", DEFAULT_CADENCE) or DEFAULT_CADENCE)


def get_codex_cadence() -> int:
    config = _load_polyglot_config()
    return int(config.get("codex_phrase_cadence", DEFAULT_CODEX_CADENCE) or DEFAULT_CODEX_CADENCE)


def get_active_pair_id() -> str | None:
    config = _load_polyglot_config()
    pair_id = config.get("active_pair_id")
    return pair_id if pair_id else None


def reset_pair_state() -> None:
    """Clear the picker history when the active pair changes so variety scoring restarts."""
    def reset(state: dict) -> None:
        state["shown_counts"] = {}
        state["recent_indices"] = []
        state["last_phrase_idx"] = -1
        state["total_phrases_shown"] = 0

    update_hook_state(reset)
