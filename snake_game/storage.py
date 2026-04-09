"""High score persistence for Snake Game."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

APP_DIR_NAME = "snake-game"


def data_dir() -> Path:
    home = Path.home()
    if sys.platform == "darwin":
        root = home / "Library" / "Application Support"
    elif os.name == "nt":
        root = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
    return root / APP_DIR_NAME


def load_high_score() -> int:
    path = data_dir() / "high_score.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return int(data.get("high_score", 0))
    except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError, ValueError):
        return 0


def save_high_score(score: int) -> None:
    path = data_dir() / "high_score.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"high_score": score}), encoding="utf-8")
