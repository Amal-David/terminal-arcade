"""Configuration accessors for the polyglot ambient hooks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from terminal_arcade.platform import app_data_dir, atomic_write_json

APP_DIR_NAME = "polyglot"

DEFAULT_CADENCE = 5
DEFAULT_CODEX_CADENCE = 5


def _state_dir() -> Path:
    return app_data_dir(APP_DIR_NAME)


HOOK_STATE_FILE = _state_dir() / "hook_state.json"


def load_hook_state() -> dict:
    try:
        return json.loads(HOOK_STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {
            "call_count": 0,
            "codex_turn_count": 0,
            "last_phrase_idx": -1,
            "shown_counts": {},
            "recent_indices": [],
            "active_pair_id": None,
            "total_phrases_shown": 0,
        }


def save_hook_state(state: dict) -> None:
    try:
        atomic_write_json(HOOK_STATE_FILE, state, indent=None)
    except OSError:
        pass


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
    state = load_hook_state()
    state["shown_counts"] = {}
    state["recent_indices"] = []
    state["last_phrase_idx"] = -1
    state["total_phrases_shown"] = 0
    save_hook_state(state)
