#!/usr/bin/env python3
"""Fail when runtime catalog metadata and public documentation drift apart."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bookshelf.data.books import load_all_books  # noqa: E402
from polyglot.data.content_loader import ALL_PAIRS  # noqa: E402
from terminal_arcade.catalog import (  # noqa: E402
    AMBIENT_CATEGORY,
    BOOK_COUNT,
    GAME_CATEGORY,
    POLYGLOT_PAIR_COUNT,
)
from terminal_arcade.launcher import build_entries  # noqa: E402


def main() -> int:
    failures: list[str] = []
    books = load_all_books()
    pairs = ALL_PAIRS
    entries = build_entries()
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    polyglot_readme = (PROJECT_ROOT / "polyglot" / "README.md").read_text(encoding="utf-8")
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    if len(books) != BOOK_COUNT:
        failures.append(f"BOOK_COUNT={BOOK_COUNT}, runtime={len(books)}")
    if len(pairs) != POLYGLOT_PAIR_COUNT:
        failures.append(f"POLYGLOT_PAIR_COUNT={POLYGLOT_PAIR_COUNT}, runtime={len(pairs)}")
    if f"{BOOK_COUNT} books" not in readme:
        failures.append(f"README does not advertise {BOOK_COUNT} books")
    if f"{POLYGLOT_PAIR_COUNT} language pairs" not in readme:
        failures.append(f"README does not advertise {POLYGLOT_PAIR_COUNT} language pairs")
    if f"{POLYGLOT_PAIR_COUNT} language pairs" not in polyglot_readme:
        failures.append(
            f"polyglot/README.md does not advertise {POLYGLOT_PAIR_COUNT} language pairs"
        )

    categories = [entry.category for entry in entries]
    if categories != [GAME_CATEGORY] * 6 + [AMBIENT_CATEGORY] * 3:
        failures.append(f"unexpected launcher categories: {categories}")

    for classifier in (
        '"Operating System :: MacOS"',
        '"Operating System :: POSIX :: Linux"',
    ):
        if classifier not in pyproject:
            failures.append(f"pyproject.toml is missing {classifier}")
    if "Windows is not currently supported." not in readme:
        failures.append("README does not state the Windows support policy")
    for stale_instruction in ("```powershell", "py -m", "| Windows |", "# Windows"):
        if stale_instruction in readme:
            failures.append(f"README still contains Windows instructions: {stale_instruction}")

    if failures:
        for failure in failures:
            print(f"catalog drift: {failure}", file=sys.stderr)
        return 1

    print(
        f"Catalog metadata is current: {BOOK_COUNT} books, "
        f"{POLYGLOT_PAIR_COUNT} language pairs, {len(entries)} cabinets."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
