"""Configuration for the ambient quote hook."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from terminal_arcade.platform import app_data_dir, atomic_write_json, locked_json_update

# State lives in a durable location, not /tmp/
APP_DIR_NAME = "bookshelf"

# Defaults (overridden by user config)
DEFAULT_CADENCE = 5
DEFAULT_CODEX_CADENCE = 5
DEFAULT_CONTEXT_MATCHING = True


def _state_dir() -> Path:
    """Platform-aware state directory (same as bookshelf storage)."""
    return app_data_dir(APP_DIR_NAME)


HOOK_STATE_FILE = _state_dir() / "hook_state.json"

DEFAULT_HOOK_STATE = {
    "call_count": 0,
    "codex_turn_count": 0,
    "last_quote_idx": -1,
    "shown_counts": {},
    "recent_indices": [],
    "total_quotes_shown": 0,
}


def load_hook_state() -> dict:
    """Load hook state (call counter, shown history, etc.)."""
    try:
        return json.loads(HOOK_STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return dict(DEFAULT_HOOK_STATE)


def save_hook_state(state: dict) -> None:
    """Save hook state."""
    try:
        atomic_write_json(HOOK_STATE_FILE, state, indent=None)
    except OSError:
        pass


def update_hook_state(update):
    """Run a hook-state read/modify/write transaction under an exclusive lock."""
    return locked_json_update(HOOK_STATE_FILE, DEFAULT_HOOK_STATE, update, indent=None)


def get_cadence() -> int:
    """Get the configured quote cadence (every Nth tool call)."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from bookshelf.storage import load_config
        config = load_config()
        return config.get("quote_cadence", DEFAULT_CADENCE)
    except Exception:
        return DEFAULT_CADENCE


def is_context_matching_enabled() -> bool:
    """Check if context matching is enabled."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from bookshelf.storage import load_config
        config = load_config()
        return config.get("context_matching", DEFAULT_CONTEXT_MATCHING)
    except Exception:
        return DEFAULT_CONTEXT_MATCHING


def get_codex_cadence() -> int:
    """Get the configured Codex quote cadence (every Nth turn-ended event)."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from bookshelf.storage import load_config
        config = load_config()
        return config.get("codex_quote_cadence", DEFAULT_CODEX_CADENCE)
    except Exception:
        return DEFAULT_CODEX_CADENCE
