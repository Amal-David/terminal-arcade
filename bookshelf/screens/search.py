"""Search screen — live-filter books by title or author."""

from __future__ import annotations

import curses

from bookshelf.data.books import Book, filter_books
from bookshelf.ui.ascii_art import GENRE_ICONS, truncate
from bookshelf.ui.colors import (
    BODY_TEXT,
    GENRE_COLORS,
    SEARCH_INPUT,
    SHELF_FRAME,
    TITLE_HIGHLIGHT,
)
from bookshelf.ui.widgets import draw_status_bar, safe_addstr


class SearchScreen:
    """Search and filter books by title or author."""

    def __init__(self, books: list[Book]):
        self.all_books = books
        self.query = ""
        self.results: list[Book] = list(books)
        self.cursor = 0
        self.scroll_offset = 0

    def _update_results(self) -> None:
        self.results = filter_books(self.all_books, query=self.query if self.query else None)
        self.cursor = min(self.cursor, max(0, len(self.results) - 1))
        self.scroll_offset = 0

    def selected_book(self) -> Book | None:
        if 0 <= self.cursor < len(self.results):
            return self.results[self.cursor]
        return None

    def handle_input(self, key: int) -> str | None:
        """Handle input. Returns action string or None.

        Actions: 'back', 'open'
        """
        if key == 27:  # Esc
            return "back"
        elif key in (curses.KEY_UP,):
            self.cursor = max(0, self.cursor - 1)
        elif key in (curses.KEY_DOWN,):
            self.cursor = min(len(self.results) - 1, self.cursor + 1)
        elif key in (10, 13, curses.KEY_ENTER):
            if self.results:
                return "open"
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if self.query:
                self.query = self.query[:-1]
                self._update_results()
        elif 32 <= key <= 126:
            self.query += chr(key)
            self._update_results()

        return None

    def render(self, stdscr) -> None:
        h, w = stdscr.getmaxyx()
        stdscr.erase()

        # Search header
        safe_addstr(
            stdscr, 1, 2, " SEARCH BOOKS ",
            curses.color_pair(TITLE_HIGHLIGHT) | curses.A_BOLD,
        )

        # Search input
        prompt = " 🔍 "
        input_w = min(w - 8, 60)
        safe_addstr(stdscr, 3, 2, prompt, curses.color_pair(SHELF_FRAME))
        input_text = self.query + "▌"
        padded = input_text.ljust(input_w)
        safe_addstr(stdscr, 3, 2 + len(prompt), padded, curses.color_pair(SEARCH_INPUT))

        # Result count
        count_text = f" {len(self.results)} results"
        safe_addstr(stdscr, 3, 2 + len(prompt) + input_w + 1, count_text, curses.A_DIM)

        # Separator
        safe_addstr(
            stdscr, 5, 1, "─" * (w - 2),
            curses.color_pair(SHELF_FRAME) | curses.A_DIM,
        )

        # Results list
        list_start = 6
        visible_rows = h - list_start - 2

        if visible_rows <= 0:
            return

        # Adjust scroll
        if self.cursor < self.scroll_offset:
            self.scroll_offset = self.cursor
        elif self.cursor >= self.scroll_offset + visible_rows:
            self.scroll_offset = self.cursor - visible_rows + 1

        for i in range(visible_rows):
            book_idx = self.scroll_offset + i
            if book_idx >= len(self.results):
                break

            book = self.results[book_idx]
            row_y = list_start + i
            is_selected = book_idx == self.cursor

            genre_icon = GENRE_ICONS.get(book.genre, "●")
            title_part = truncate(book.title, 35)
            author_part = truncate(book.author, 25)

            line = f"  {genre_icon} {title_part:<36} {author_part:<26} {book.year}"

            if is_selected:
                safe_addstr(
                    stdscr, row_y, 0, line.ljust(w - 1),
                    curses.A_REVERSE | curses.A_BOLD,
                )
            else:
                safe_addstr(stdscr, row_y, 0, line, curses.color_pair(BODY_TEXT))

        # Status bar
        draw_status_bar(stdscr, " Type to search  ↑↓: Navigate  Enter: Open  Esc: Back")
