from __future__ import annotations

import json
import os
import sys
from pathlib import Path


APP_DIR_NAME = "dino-run"
HIGH_SCORE_FILE = "high_score.json"


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
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"high_score": max(0, int(score))}
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
