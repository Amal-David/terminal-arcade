"""Configuration accessors for the polyglot ambient hooks."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

APP_DIR_NAME = "polyglot"

DEFAULT_CADENCE = 5
DEFAULT_CODEX_CADENCE = 5


def _state_dir() -> Path:
    home = Path.home()
    if sys.platform == "darwin":
        root = home / "Library" / "Application Support"
    elif os.name == "nt":
        root = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
    return root / APP_DIR_NAME


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
        HOOK_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        HOOK_STATE_FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
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
