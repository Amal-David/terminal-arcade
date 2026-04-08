"""Configuration for the ambient quote hook."""

from __future__ import annotations

import json
import os
from pathlib import Path

HOOK_STATE_FILE = Path("/tmp/bookshelf_hook_state.json")

# Defaults (overridden by user config in ~/Library/Application Support/bookshelf/config.json)
DEFAULT_CADENCE = 5
DEFAULT_CONTEXT_MATCHING = True


def load_hook_state() -> dict:
    """Load hook state (tool call counter, last quote index)."""
    try:
        return json.loads(HOOK_STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"call_count": 0, "last_quote_idx": -1}


def save_hook_state(state: dict) -> None:
    """Save hook state."""
    try:
        HOOK_STATE_FILE.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        pass


def get_cadence() -> int:
    """Get the configured quote cadence (every Nth tool call)."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from bookshelf.storage import load_config
        config = load_config()
        return config.get("quote_cadence", DEFAULT_CADENCE)
    except Exception:
        return DEFAULT_CADENCE


def is_context_matching_enabled() -> bool:
    """Check if context matching is enabled."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from bookshelf.storage import load_config
        config = load_config()
        return config.get("context_matching", DEFAULT_CONTEXT_MATCHING)
    except Exception:
        return DEFAULT_CONTEXT_MATCHING
