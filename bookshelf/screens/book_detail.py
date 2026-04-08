"""Book detail screen — shows summary, quotes, and metadata."""

from __future__ import annotations

import curses
import random

from bookshelf.data.books import Book
from bookshelf.ui.ascii_art import GENRE_ICONS, truncate, wrap_text
from bookshelf.ui.colors import (
    BODY_TEXT,
    FAVORITE_HEART,
    GENRE_COLORS,
    MOOD_TAG,
    QUOTE_TEXT,
    SHELF_FRAME,
    TITLE_HIGHLIGHT,
)
from bookshelf.ui.widgets import (
    draw_centered,
    draw_mood_tags,
    draw_status_bar,
    safe_addstr,
)


class BookDetailScreen:
    """Detailed view of a single book."""

    def __init__(self, book: Book, quotes: list, favorites: list[str]):
        self.book = book
        self.quotes = quotes
        self.favorites = favorites
        self.quote_idx = random.randint(0, max(0, len(quotes) - 1)) if quotes else 0
        self.scroll_offset = 0

    @property
    def is_favorite(self) -> bool:
        return self.book.title in self.favorites

    def handle_input(self, key: int) -> str | None:
        """Handle input. Returns action string or None.

        Actions: 'back', 'toggle_fav', 'mark_read', 'mark_want'
        """
        if key in (27, ord("q"), ord("Q"), curses.KEY_LEFT, curses.KEY_BACKSPACE, 127):
            return "back"
        elif key in (ord("f"), ord("F")):
            if self.book.title in self.favorites:
                self.favorites.remove(self.book.title)
            else:
                self.favorites.append(self.book.title)
            return "toggle_fav"
        elif key in (curses.KEY_RIGHT, ord("n"), ord("N")):
            if self.quotes:
                self.quote_idx = (self.quote_idx + 1) % len(self.quotes)
        elif key in (ord("p"), ord("P")):
            if self.quotes:
                self.quote_idx = (self.quote_idx - 1) % len(self.quotes)
        elif key in (curses.KEY_DOWN, ord("j")):
            self.scroll_offset += 1
        elif key in (curses.KEY_UP, ord("k")):
            self.scroll_offset = max(0, self.scroll_offset - 1)
        elif key in (ord("m"), ord("M")):
            return "mark_read"
        elif key in (ord("w"), ord("W")):
            return "mark_want"

        return None

    def render(self, stdscr) -> None:
        h, w = stdscr.getmaxyx()
        stdscr.erase()

        content_w = min(w - 4, 76)
        margin = max(1, (w - content_w) // 2)
        y = 1 - self.scroll_offset

        # Title
        if 0 <= y < h - 1:
            title = truncate(self.book.title, content_w)
            safe_addstr(
                stdscr, y, margin, title,
                curses.color_pair(TITLE_HIGHLIGHT) | curses.A_BOLD,
            )
        y += 1

        # Author and year
        if 0 <= y < h - 1:
            byline = f"by {self.book.author} ({self.book.year})"
            safe_addstr(stdscr, y, margin, byline, curses.color_pair(BODY_TEXT))
        y += 1

        # Genre badge and favorite heart
        if 0 <= y < h - 1:
            genre_icon = GENRE_ICONS.get(self.book.genre, "●")
            genre_color = GENRE_COLORS.get(self.book.genre, BODY_TEXT)
            safe_addstr(
                stdscr, y, margin,
                f"{genre_icon} {self.book.genre.title()}",
                curses.color_pair(genre_color) | curses.A_BOLD,
            )
            if self.is_favorite:
                safe_addstr(
                    stdscr, y, margin + len(self.book.genre) + 4,
                    " ♥ Favorite",
                    curses.color_pair(FAVORITE_HEART) | curses.A_BOLD,
                )
        y += 1

        # Mood tags
        if 0 <= y < h - 1 and self.book.mood:
            draw_mood_tags(stdscr, y, margin, self.book.mood, content_w)
        y += 2

        # Separator
        if 0 <= y < h - 1:
            safe_addstr(
                stdscr, y, margin, "─" * content_w,
                curses.color_pair(SHELF_FRAME) | curses.A_DIM,
            )
        y += 1

        # Summary header
        if 0 <= y < h - 1:
            safe_addstr(
                stdscr, y, margin, "SUMMARY",
                curses.color_pair(SHELF_FRAME) | curses.A_BOLD,
            )
        y += 1

        # Summary text (word-wrapped)
        summary_lines = wrap_text(self.book.summary, content_w)
        for line in summary_lines:
            if 0 <= y < h - 1:
                safe_addstr(stdscr, y, margin, line, curses.color_pair(BODY_TEXT))
            y += 1

        y += 1

        # Quotes section
        if 0 <= y < h - 1:
            safe_addstr(
                stdscr, y, margin, "─" * content_w,
                curses.color_pair(SHELF_FRAME) | curses.A_DIM,
            )
        y += 1

        if self.quotes:
            # Quote header with navigation
            if 0 <= y < h - 1:
                header = f"QUOTES  [{self.quote_idx + 1}/{len(self.quotes)}]"
                safe_addstr(
                    stdscr, y, margin, header,
                    curses.color_pair(SHELF_FRAME) | curses.A_BOLD,
                )
                nav_hint = "← → to browse"
                safe_addstr(
                    stdscr, y, margin + content_w - len(nav_hint),
                    nav_hint, curses.A_DIM,
                )
            y += 1

            # Current quote
            quote = self.quotes[self.quote_idx]
            quote_text = f'"{quote.text}"'
            quote_lines = wrap_text(quote_text, content_w - 4)

            y += 1
            for line in quote_lines:
                if 0 <= y < h - 1:
                    safe_addstr(
                        stdscr, y, margin + 2, line,
                        curses.color_pair(QUOTE_TEXT) | curses.A_ITALIC
                        if hasattr(curses, "A_ITALIC")
                        else curses.color_pair(QUOTE_TEXT),
                    )
                y += 1

            # Quote attribution
            if quote.chapter and 0 <= y < h - 1:
                safe_addstr(
                    stdscr, y, margin + 4,
                    f"— {quote.chapter}",
                    curses.A_DIM,
                )
                y += 1

            # Tags
            if quote.tags and 0 <= y + 1 < h - 1:
                y += 1
                tags_str = "  ".join(f"#{t}" for t in quote.tags[:5])
                safe_addstr(
                    stdscr, y, margin + 2, tags_str,
                    curses.color_pair(MOOD_TAG) | curses.A_DIM,
                )
        else:
            if 0 <= y < h - 1:
                safe_addstr(
                    stdscr, y, margin, "No quotes available for this book.",
                    curses.A_DIM,
                )

        # Status bar
        fav_hint = "f: Unfavorite" if self.is_favorite else "f: Favorite"
        status = f" Esc/←: Back  ←→: Quotes  {fav_hint}  m: Mark Read  w: Want to Read"
        draw_status_bar(stdscr, status)
