#!/usr/bin/env python3
"""Configure how often the bookshelf hooks surface a quote.

Both the Claude Code PostToolUse hook and the Codex turn-ended hook fire
every Nth event. The default is 5. Common values are 5, 10, and 20 — flip
between them with this CLI instead of hand-editing the config.

Usage:
    python3 -m bookshelf.skill.cadence              # show current values
    python3 -m bookshelf.skill.cadence 10           # set Claude cadence to 10
    python3 -m bookshelf.skill.cadence 20 --codex   # set Codex cadence to 20
    python3 -m bookshelf.skill.cadence 10 --both    # set both cadences to 10

The integer must be >= 1. Setting to 1 fires every event (chatty); 5 is the
default; 10–20 is calmer.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bookshelf.storage import load_config, save_config  # noqa: E402


CLAUDE_KEY = "quote_cadence"
CODEX_KEY = "codex_quote_cadence"


def _show(config: dict) -> None:
    claude = config.get(CLAUDE_KEY, 5)
    codex = config.get(CODEX_KEY, 5)
    print(f"Claude Code (PostToolUse):   every {claude} tool call{'s' if claude != 1 else ''}")
    print(f"Codex (turn-ended):          every {codex} turn{'s' if codex != 1 else ''}")
    print()
    print("Common values: 5 (default), 10, 20.  Set with:")
    print("  python3 -m bookshelf.skill.cadence 10           # Claude")
    print("  python3 -m bookshelf.skill.cadence 10 --codex   # Codex")
    print("  python3 -m bookshelf.skill.cadence 10 --both    # both")


def _apply(value: int, *, codex: bool, both: bool) -> dict:
    config = load_config()
    if both or (not codex):
        config[CLAUDE_KEY] = value
    if both or codex:
        config[CODEX_KEY] = value
    save_config(config)
    return config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bookshelf.skill.cadence",
        description="Set how often the bookshelf hooks surface a quote.",
    )
    parser.add_argument(
        "value",
        type=int,
        nargs="?",
        help="Cadence (>=1). Common values: 5, 10, 20. Omit to show current.",
    )
    target = parser.add_mutually_exclusive_group()
    target.add_argument(
        "--codex",
        action="store_true",
        help="Apply only to the Codex hook (default applies to Claude Code).",
    )
    target.add_argument(
        "--both",
        action="store_true",
        help="Apply to both Claude Code and Codex hooks.",
    )
    args = parser.parse_args(argv)

    if args.value is None:
        _show(load_config())
        return 0

    if args.value < 1:
        parser.error("cadence must be >= 1")

    config = _apply(args.value, codex=args.codex, both=args.both)
    _show(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
