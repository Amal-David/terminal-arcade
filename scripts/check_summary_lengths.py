#!/usr/bin/env python3
"""Report (and gate on) any book whose summary is below the word floor.

Usage:
    python3 scripts/check_summary_lengths.py            # default floor 150
    python3 scripts/check_summary_lengths.py --floor 300
    python3 scripts/check_summary_lengths.py --genre romance
    python3 scripts/check_summary_lengths.py --json     # machine-readable

Exits non-zero when any book's summary has fewer than ``--floor`` words,
which makes it usable as a pre-commit / CI gate.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running directly: python3 scripts/check_summary_lengths.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bookshelf.data.books import load_all_books  # noqa: E402


def word_count(text: str) -> int:
    return len(text.split())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--floor", type=int, default=150, help="Minimum word count (default 150)")
    parser.add_argument("--genre", type=str, default=None, help="Limit to a single genre")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    books = load_all_books()
    if args.genre:
        books = [b for b in books if b.genre == args.genre]

    short = [b for b in books if word_count(b.summary) < args.floor]

    if args.json:
        payload = {
            "floor": args.floor,
            "checked": len(books),
            "below_floor": len(short),
            "books": [
                {
                    "title": b.title,
                    "author": b.author,
                    "genre": b.genre,
                    "words": word_count(b.summary),
                }
                for b in short
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"Floor: {args.floor} words")
        print(f"Checked: {len(books)} books")
        print(f"Below floor: {len(short)}")
        if short:
            print()
            by_genre: dict[str, list] = {}
            for b in short:
                by_genre.setdefault(b.genre, []).append(b)
            for genre in sorted(by_genre):
                print(f"  {genre}: {len(by_genre[genre])}")
            print()
            print("Shortest 30:")
            for b in sorted(short, key=lambda x: word_count(x.summary))[:30]:
                print(f"  [{word_count(b.summary):3d}] {b.genre:11s} {b.title} — {b.author}")

    return 1 if short else 0


if __name__ == "__main__":
    raise SystemExit(main())
