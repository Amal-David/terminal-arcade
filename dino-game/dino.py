#!/usr/bin/env python3
"""Backward-compatible launcher for the packaged game."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dino_game.game import run


if __name__ == "__main__":
    run()
