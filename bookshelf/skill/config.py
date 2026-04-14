"""Configuration for the ambient quote hook."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# State lives in a durable location, not /tmp/
APP_DIR_NAME = "bookshelf"

# Defaults (overridden by user config)
DEFAULT_CADENCE = 5
DEFAULT_CONTEXT_MATCHING = True


def _state_dir() -> Path:
    """Platform-aware state directory (same as bookshelf storage)."""
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
    """Load hook state (call counter, shown history, etc.)."""
    try:
        return json.loads(HOOK_STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"call_count": 0, "last_quote_idx": -1, "shown_counts": {}, "recent_indices": []}


def save_hook_state(state: dict) -> None:
    """Save hook state."""
    try:
        HOOK_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        HOOK_STATE_FILE.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        pass


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
