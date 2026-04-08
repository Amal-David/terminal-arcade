"""Collection screen — shows favorites and reading lists."""

from __future__ import annotations

import curses

from bookshelf.data.books import Book
from bookshelf.ui.ascii_art import GENRE_ICONS, truncate
from bookshelf.ui.colors import (
    BODY_TEXT,
    FAVORITE_HEART,
    GENRE_COLORS,
    SHELF_FRAME,
    TITLE_HIGHLIGHT,
)
from bookshelf.ui.widgets import draw_centered, draw_status_bar, safe_addstr

TABS = ["Favorites", "Read", "Want to Read", "Stats"]


class CollectionScreen:
    """User's personal book collection."""

    def __init__(
        self,
        books: list[Book],
        favorites: list[str],
        read_list: list[str],
        want_list: list[str],
        stats: dict,
    ):
        self.all_books = books
        self.favorites = favorites
        self.read_list = read_list
        self.want_list = want_list
        self.stats = stats
        self.tab_idx = 0
        self.cursor = 0
        self.scroll_offset = 0

    def _current_list(self) -> list[Book]:
        """Get the book list for the current tab."""
        if self.tab_idx == 0:
            titles = set(self.favorites)
        elif self.tab_idx == 1:
            titles = set(self.read_list)
        elif self.tab_idx == 2:
            titles = set(self.want_list)
        else:
            return []

        return [b for b in self.all_books if b.title in titles]

    def selected_book(self) -> Book | None:
        books = self._current_list()
        if 0 <= self.cursor < len(books):
            return books[self.cursor]
        return None

    def handle_input(self, key: int) -> str | None:
        """Handle input. Returns action string or None.

        Actions: 'back', 'open'
        """
        if key in (27, ord("q"), ord("Q"), curses.KEY_BACKSPACE, 127):
            return "back"
        elif key == 9:  # Tab
            self.tab_idx = (self.tab_idx + 1) % len(TABS)
            self.cursor = 0
            self.scroll_offset = 0
        elif key in (curses.KEY_BTAB,):
            self.tab_idx = (self.tab_idx - 1) % len(TABS)
            self.cursor = 0
            self.scroll_offset = 0
        elif key in (curses.KEY_UP, ord("k")):
            self.cursor = max(0, self.cursor - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            books = self._current_list()
            self.cursor = min(len(books) - 1, self.cursor + 1)
        elif key in (10, 13, curses.KEY_ENTER):
            if self._current_list():
                return "open"

        return None

    def render(self, stdscr) -> None:
        h, w = stdscr.getmaxyx()
        stdscr.erase()

        # Title
        safe_addstr(
            stdscr, 1, 2, " MY COLLECTION ",
            curses.color_pair(TITLE_HIGHLIGHT) | curses.A_BOLD,
        )

        # Tabs
        tab_x = 2
        for i, tab in enumerate(TABS):
            label = f" {tab} "
            if i == self.tab_idx:
                safe_addstr(stdscr, 3, tab_x, label, curses.A_REVERSE | curses.A_BOLD)
            else:
                safe_addstr(stdscr, 3, tab_x, label, curses.A_DIM)
            tab_x += len(label) + 1

        # Separator
        safe_addstr(
            stdscr, 4, 1, "─" * (w - 2),
            curses.color_pair(SHELF_FRAME) | curses.A_DIM,
        )

        if self.tab_idx == 3:
            # Stats view
            self._render_stats(stdscr)
        else:
            # Book list view
            self._render_book_list(stdscr)

        draw_status_bar(stdscr, " Tab: Switch Section  ↑↓: Navigate  Enter: Open  Esc: Back")

    def _render_stats(self, stdscr) -> None:
        h, w = stdscr.getmaxyx()
        y = 6

        stats = [
            ("Books Explored", str(self.stats.get("books_explored", 0))),
            ("Quotes Seen", str(self.stats.get("quotes_seen", 0))),
            ("Favorites", str(len(self.favorites))),
            ("Books Read", str(len(self.read_list))),
            ("Want to Read", str(len(self.want_list))),
            ("Total in Library", str(len(self.all_books))),
        ]

        for label, value in stats:
            if y >= h - 2:
                break
            safe_addstr(
                stdscr, y, 4, f"{label}:", curses.color_pair(BODY_TEXT),
            )
            safe_addstr(
                stdscr, y, 25, value,
                curses.color_pair(TITLE_HIGHLIGHT) | curses.A_BOLD,
            )
            y += 2

    def _render_book_list(self, stdscr) -> None:
        h, w = stdscr.getmaxyx()
        books = self._current_list()

        list_start = 5
        visible_rows = h - list_start - 2

        if not books:
            empty_msg = "No books here yet. Browse the shelf and add some!"
            draw_centered(stdscr, list_start + 2, empty_msg, curses.A_DIM)
            return

        if visible_rows <= 0:
            return

        # Adjust scroll
        if self.cursor < self.scroll_offset:
            self.scroll_offset = self.cursor
        elif self.cursor >= self.scroll_offset + visible_rows:
            self.scroll_offset = self.cursor - visible_rows + 1

        for i in range(visible_rows):
            book_idx = self.scroll_offset + i
            if book_idx >= len(books):
                break

            book = books[book_idx]
            row_y = list_start + i
            is_selected = book_idx == self.cursor

            genre_icon = GENRE_ICONS.get(book.genre, "●")
            title_part = truncate(book.title, 35)
            author_part = truncate(book.author, 25)

            line = f"  ♥ {genre_icon} {title_part:<36} {author_part}"

            if is_selected:
                safe_addstr(
                    stdscr, row_y, 0, line.ljust(w - 1),
                    curses.A_REVERSE | curses.A_BOLD,
                )
            else:
                safe_addstr(
                    stdscr, row_y, 2, "♥",
                    curses.color_pair(FAVORITE_HEART) | curses.A_BOLD,
                )
                safe_addstr(
                    stdscr, row_y, 4, f" {genre_icon} ",
                    curses.color_pair(GENRE_COLORS.get(book.genre, BODY_TEXT)),
                )
                safe_addstr(
                    stdscr, row_y, 8, f"{title_part:<36} {author_part}",
                    curses.color_pair(BODY_TEXT),
                )
