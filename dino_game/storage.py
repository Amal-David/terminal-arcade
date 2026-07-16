from __future__ import annotations

import json
from pathlib import Path

from terminal_arcade.platform import app_data_dir, atomic_write_json


APP_DIR_NAME = "dino-run"
HIGH_SCORE_FILE = "high_score.json"


def data_dir(base_dir: Path | None = None) -> Path:
    return app_data_dir(APP_DIR_NAME, base_dir)


def score_file_path(base_dir: Path | None = None) -> Path:
    return data_dir(base_dir) / HIGH_SCORE_FILE


def load_high_score(base_dir: Path | None = None) -> int:
    score_path = score_file_path(base_dir)
    try:
        payload = json.loads(score_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return 0
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return 0

    score = payload.get("high_score", 0)
    if not isinstance(score, int):
        return 0
    return max(0, score)


def save_high_score(score: int, base_dir: Path | None = None) -> None:
    target = score_file_path(base_dir)
    payload = {"high_score": max(0, int(score))}
    atomic_write_json(target, payload)
