#!/usr/bin/env python3
"""Configure how often the wonder hooks surface today's wonder.

The Claude Code PostToolUse hook and the Codex turn-ended hook each pay
attention to a cadence value:

    daily    — fire at most once per local calendar day (the default)
    <int>    — fire every Nth event (every Nth tool call / turn)
    off      — never fire

Usage:
    python3 -m wonder.skill.cadence                # show current values
    python3 -m wonder.skill.cadence daily          # set Claude to daily
    python3 -m wonder.skill.cadence 5              # set Claude to every 5th tool call
    python3 -m wonder.skill.cadence off            # disable the Claude hook
    python3 -m wonder.skill.cadence 10 --codex     # set Codex to every 10th turn
    python3 -m wonder.skill.cadence daily --both   # set both to daily

Optionally pin a category instead of the daily rotation:
    python3 -m wonder.skill.cadence --category funny
    python3 -m wonder.skill.cadence --category rotate
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from wonder.skill.config import (  # noqa: E402
    CATEGORY_KEY,
    CLAUDE_KEY,
    CODEX_KEY,
    DEFAULT_CADENCE,
    DEFAULT_CATEGORY,
    DEFAULT_CODEX_CADENCE,
    VALID_CATEGORIES,
)
from wonder.storage import load_config, save_config  # noqa: E402


def _parse_cadence(value: str):
    v = value.strip().lower()
    if v in ("daily", "off"):
        return v
    try:
        n = int(v)
        if n >= 1:
            return n
    except ValueError:
        pass
    raise argparse.ArgumentTypeError(
        f"cadence must be 'daily', 'off', or an integer >= 1 (got {value!r})"
    )


def _describe(value) -> str:
    if value == "daily":
        return "once per day"
    if value == "off":
        return "off (never fires)"
    if isinstance(value, int):
        return f"every {value} event{'s' if value != 1 else ''}"
    return str(value)


def _show(config: dict) -> None:
    claude = config.get(CLAUDE_KEY, DEFAULT_CADENCE)
    codex = config.get(CODEX_KEY, DEFAULT_CODEX_CADENCE)
    category = config.get(CATEGORY_KEY, DEFAULT_CATEGORY)
    print(f"Claude Code (PostToolUse):   {_describe(claude)}")
    print(f"Codex (turn-ended):          {_describe(codex)}")
    print(f"Category:                    {category}")
    print()
    print("Common values: daily (default), off, or 5 / 10 / 20. Examples:")
    print("  python3 -m wonder.skill.cadence daily")
    print("  python3 -m wonder.skill.cadence 10 --codex")
    print("  python3 -m wonder.skill.cadence off --both")
    print("  python3 -m wonder.skill.cadence --category funny")


def _apply_cadence(config: dict, value, *, codex: bool, both: bool) -> dict:
    if both or not codex:
        config[CLAUDE_KEY] = value
    if both or codex:
        config[CODEX_KEY] = value
    return config


def _apply_category(config: dict, value: str) -> dict:
    config[CATEGORY_KEY] = value
    return config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wonder.skill.cadence",
        description="Set how often the wonder hooks surface today's wonder.",
    )
    parser.add_argument(
        "value",
        type=_parse_cadence,
        nargs="?",
        help="Cadence: 'daily', 'off', or an integer >= 1. Omit to show current.",
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
    parser.add_argument(
        "--category",
        choices=sorted(VALID_CATEGORIES),
        help="Pin to a category, or use 'rotate' (default) to cycle daily.",
    )
    args = parser.parse_args(argv)

    config = load_config()
    changed = False

    if args.value is not None:
        config = _apply_cadence(config, args.value, codex=args.codex, both=args.both)
        changed = True
    if args.category is not None:
        config = _apply_category(config, args.category)
        changed = True

    if changed:
        save_config(config)

    _show(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
