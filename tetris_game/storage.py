"""High score persistence for Tetris."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


APP_DIR_NAME = "tetris-game"
SCORE_FILE = "high_score.json"


def data_dir(base_dir: Path | None = None) -> Path:
    if base_dir is not None:
        return Path(base_dir)

    home = Path.home()
    if sys.platform == "darwin":
        root = home / "Library" / "Application Support"
    elif os.name == "nt":
        root = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
    return root / APP_DIR_NAME


def load_high_score(base_dir: Path | None = None) -> int:
    path = data_dir(base_dir) / SCORE_FILE
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return max(0, int(payload.get("high_score", 0)))
    except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError, ValueError):
        return 0


def save_high_score(score: int, base_dir: Path | None = None) -> None:
    path = data_dir(base_dir) / SCORE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"high_score": max(0, int(score))}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

