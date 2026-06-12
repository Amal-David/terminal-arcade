"""Configuration and hook-state persistence for the wonder skill.

State and config live in the same platform-aware directory as the wonder app
itself (`wonder.storage.data_dir()`), so the cabinet and the ambient hook
share a single source of truth.

Cadence values:
    "daily"  — fire once per local calendar day (the default)
    int >= 1 — fire every Nth event (every Nth Claude tool call, or every Nth
               Codex turn)
    "off"    — never fire
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from wonder.storage import data_dir, load_config  # noqa: E402

DEFAULT_CADENCE = "daily"
DEFAULT_CODEX_CADENCE = "daily"
DEFAULT_CATEGORY = "rotate"  # rotate daily through funny/heart/weird/inspiring

CLAUDE_KEY = "wonder_cadence"
CODEX_KEY = "codex_wonder_cadence"
CATEGORY_KEY = "wonder_category"

HOOK_STATE_FILE = "hook_state.json"

VALID_CATEGORIES = {"rotate", "funny", "heartwarming", "weird", "inspiring", "surprise"}


def _state_path() -> Path:
    return data_dir() / HOOK_STATE_FILE


def load_hook_state() -> dict:
    try:
        return json.loads(_state_path().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_hook_state(state: dict) -> None:
    path = _state_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError:
        pass


def _normalize_cadence(value, default):
    if value is None:
        return default
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("daily", "off"):
            return v
        try:
            n = int(v)
            if n >= 1:
                return n
        except ValueError:
            pass
        return default
    if isinstance(value, int) and value >= 1:
        return value
    return default


def get_cadence() -> str | int:
    cfg = load_config()
    return _normalize_cadence(cfg.get(CLAUDE_KEY), DEFAULT_CADENCE)


def get_codex_cadence() -> str | int:
    cfg = load_config()
    return _normalize_cadence(cfg.get(CODEX_KEY), DEFAULT_CODEX_CADENCE)


def get_category_preference() -> str:
    cfg = load_config()
    value = cfg.get(CATEGORY_KEY, DEFAULT_CATEGORY)
    if isinstance(value, str) and value.strip().lower() in VALID_CATEGORIES:
        return value.strip().lower()
    return DEFAULT_CATEGORY
