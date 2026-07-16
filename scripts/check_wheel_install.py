#!/usr/bin/env python3
"""Install a built wheel in isolation and smoke-test every shipped cabinet."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

MODULES = (
    "terminal_arcade",
    "dino_game",
    "snake_game",
    "tetris_game",
    "chess_game",
    "star_blast",
    "kombat_game",
    "bookshelf",
    "wonder",
    "polyglot",
)

SMOKE_PROGRAM = """
import importlib
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
for module_name in sys.argv[2:]:
    importlib.import_module(module_name)

from dino_game.audio import AUDIO_DIR as dino_audio
from star_blast.audio import AUDIO_DIR as star_audio

required = (dino_audio / "jump.wav", star_audio / "laser.wav")
missing = [str(path) for path in required if not Path(path).is_file()]
if missing:
    raise SystemExit("missing wheel resources: " + ", ".join(missing))
print("Imported every cabinet and resolved package-owned audio resources.")
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    args = parser.parse_args()
    wheel = args.wheel.resolve()
    if not wheel.is_file():
        parser.error(f"wheel does not exist: {wheel}")

    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "site-packages"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-deps",
                "--target",
                str(target),
                str(wheel),
            ],
            check=True,
            cwd=tmp,
        )
        subprocess.run(
            [sys.executable, "-I", "-c", SMOKE_PROGRAM, str(target), *MODULES],
            check=True,
            cwd=tmp,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
