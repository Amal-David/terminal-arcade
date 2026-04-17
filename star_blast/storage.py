"""High score persistence for Star Blast."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


APP_DIR_NAME = "star-blast"
SCORES_FILE = "scores.json"
DEFAULT_SCORES = {
    "campaign_high_score": 0,
    "endless_high_score": 0,
}


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


def load_scores(base_dir: Path | None = None) -> dict[str, int]:
    path = data_dir(base_dir) / SCORES_FILE
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError, ValueError):
        return dict(DEFAULT_SCORES)

    if not isinstance(payload, dict):
        return dict(DEFAULT_SCORES)

    merged = dict(DEFAULT_SCORES)
    for key in DEFAULT_SCORES:
        value = payload.get(key, DEFAULT_SCORES[key])
        try:
            merged[key] = max(0, int(value))
        except (TypeError, ValueError):
            merged[key] = DEFAULT_SCORES[key]
    return merged


def save_scores(scores: dict[str, int], base_dir: Path | None = None) -> None:
    path = data_dir(base_dir) / SCORES_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "campaign_high_score": max(0, int(scores.get("campaign_high_score", 0))),
        "endless_high_score": max(0, int(scores.get("endless_high_score", 0))),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
