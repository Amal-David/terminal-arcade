import unittest

from bookshelf.data.quotes import QUOTES, Quote
from bookshelf.skill.hook import format_quote_message, select_quote_index


class BookshelfHookTests(unittest.TestCase):
    def test_select_quote_index_prefers_unseen_quotes_before_repeats(self) -> None:
        quotes = [
            Quote("Seen quote", "Book A", "Author A", "", ["focus"]),
            Quote("Unseen quote 1", "Book B", "Author B", "", []),
            Quote("Unseen quote 2", "Book C", "Author C", "", []),
        ]

        idx = select_quote_index(
            quotes,
            shown_counts={"0": 4},
            recent_indices=[],
            context_tags=["focus"],
        )

        self.assertIn(idx, {1, 2})

    def test_format_quote_message_uses_current_quote_total(self) -> None:
        message = format_quote_message(
            {
                "text": "Stay hungry, stay foolish.",
                "author": "Steve Jobs",
                "book": "Collected Talks",
                "tags": ["ambition", "creativity"],
                "unique_shown": 12,
            },
            len(QUOTES),
        )

        self.assertIn(f"[12/{len(QUOTES)} unique quotes shown]", message)


if __name__ == "__main__":
    unittest.main()
