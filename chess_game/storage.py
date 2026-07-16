"""Persistent stats storage for the chess cabinet."""

from __future__ import annotations

import json
from pathlib import Path

from terminal_arcade.platform import app_data_dir, atomic_write_json


APP_DIR_NAME = "chess-game"
STATS_FILE = "stats.json"
DEFAULT_STATS = {
    "last_difficulty": "medium",
    "wins": {"easy": 0, "medium": 0, "hard": 0},
    "losses": {"easy": 0, "medium": 0, "hard": 0},
    "draws": {"easy": 0, "medium": 0, "hard": 0},
}


def data_dir(base_dir: Path | None = None) -> Path:
    return app_data_dir(APP_DIR_NAME, base_dir)


def normalize_stats(raw: object) -> dict[str, object]:
    stats = json.loads(json.dumps(DEFAULT_STATS))
    if not isinstance(raw, dict):
        return stats

    last = raw.get("last_difficulty")
    if last in ("easy", "medium", "hard"):
        stats["last_difficulty"] = last

    for bucket in ("wins", "losses", "draws"):
        value = raw.get(bucket)
        if not isinstance(value, dict):
            continue
        for level in ("easy", "medium", "hard"):
            try:
                stats[bucket][level] = max(0, int(value.get(level, 0)))
            except (TypeError, ValueError):
                stats[bucket][level] = 0
    return stats


def load_stats(base_dir: Path | None = None) -> dict[str, object]:
    path = data_dir(base_dir) / STATS_FILE
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError, ValueError):
        return normalize_stats(None)
    return normalize_stats(payload)


def save_stats(stats: dict[str, object], base_dir: Path | None = None) -> None:
    path = data_dir(base_dir) / STATS_FILE
    normalized = normalize_stats(stats)
    atomic_write_json(path, normalized)
