"""High score persistence for Tetris."""

from __future__ import annotations

import json
from pathlib import Path

from terminal_arcade.platform import app_data_dir, atomic_write_json


APP_DIR_NAME = "tetris-game"
SCORE_FILE = "high_score.json"


def data_dir(base_dir: Path | None = None) -> Path:
    return app_data_dir(APP_DIR_NAME, base_dir)


def load_high_score(base_dir: Path | None = None) -> int:
    path = data_dir(base_dir) / SCORE_FILE
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return max(0, int(payload.get("high_score", 0)))
    except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError, ValueError):
        return 0


def save_high_score(score: int, base_dir: Path | None = None) -> None:
    path = data_dir(base_dir) / SCORE_FILE
    payload = {"high_score": max(0, int(score))}
    atomic_write_json(path, payload)
