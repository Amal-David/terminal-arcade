"""High score persistence for Snake Game."""

from __future__ import annotations

import json
from pathlib import Path

from terminal_arcade.platform import app_data_dir, atomic_write_json

APP_DIR_NAME = "snake-game"


def data_dir() -> Path:
    return app_data_dir(APP_DIR_NAME)


def load_high_score() -> int:
    path = data_dir() / "high_score.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return int(data.get("high_score", 0))
    except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError, ValueError):
        return 0


def save_high_score(score: int) -> None:
    path = data_dir() / "high_score.json"
    atomic_write_json(path, {"high_score": score}, indent=None)
