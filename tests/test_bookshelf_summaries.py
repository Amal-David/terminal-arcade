"""Regression guard: every book must carry a substantive summary.

Locks the floor at 150 words so future entries can't reintroduce one-line
blurbs. If you intentionally need to lower the floor, change FLOOR here
with a comment explaining why.
"""

import unittest

from bookshelf.data.books import load_all_books

FLOOR = 150


class BookshelfSummaryLengthTests(unittest.TestCase):
    def test_every_summary_meets_word_floor(self) -> None:
        books = load_all_books()
        offenders = [
            (b.title, b.author, len(b.summary.split()))
            for b in books
            if len(b.summary.split()) < FLOOR
        ]

        if offenders:
            sample = "\n".join(
                f"  [{words:3d}] {title} — {author}" for title, author, words in offenders[:20]
            )
            self.fail(
                f"{len(offenders)}/{len(books)} books have summaries below {FLOOR} words. "
                f"First {min(20, len(offenders))} shown:\n{sample}"
            )


if __name__ == "__main__":
    unittest.main()
