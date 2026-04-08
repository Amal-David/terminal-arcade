"""Bookshelf browse screen — the main view."""

from __future__ import annotations

import curses
import random

from bookshelf.data.books import Book, filter_books
from bookshelf.data.categories import GENRE_ORDER
from bookshelf.ui.ascii_art import GENRE_ICONS, TITLE_ART, truncate
from bookshelf.ui.colors import (
    BODY_TEXT,
    FAVORITE_HEART,
    GENRE_COLORS,
    SHELF_FRAME,
    TITLE_HIGHLIGHT,
)
from bookshelf.ui.widgets import (
    draw_centered,
    draw_status_bar,
    safe_addstr,
)


class ShelfScreen:
    """Main bookshelf browsing screen."""

    def __init__(self, books: list[Book], favorites: list[str]):
        self.all_books = books
        self.favorites = favorites
        self.genre_idx = 0  # index into GENRE_ORDER
        self.cursor = 0
        self.scroll_offset = 0
        self.filtered: list[Book] = []
        self._apply_filter()

    @property
    def current_genre(self) -> str:
        return GENRE_ORDER[self.genre_idx]

    def _apply_filter(self) -> None:
        genre = self.current_genre
        self.filtered = filter_books(self.all_books, genre=genre)
        self.cursor = min(self.cursor, max(0, len(self.filtered) - 1))
        self.scroll_offset = 0

    def selected_book(self) -> Book | None:
        if 0 <= self.cursor < len(self.filtered):
            return self.filtered[self.cursor]
        return None

    def random_book(self) -> Book | None:
        if self.filtered:
            idx = random.randint(0, len(self.filtered) - 1)
            self.cursor = idx
            return self.filtered[idx]
        return None

    def handle_input(self, key: int) -> str | None:
        """Handle input. Returns action string or None.

        Actions: 'open', 'search', 'collection', 'random', 'help', 'quit'
        """
        if key in (ord("q"), ord("Q"), 27):
            return "quit"
        elif key in (curses.KEY_UP, ord("k"), ord("K")):
            self.cursor = max(0, self.cursor - 1)
        elif key in (curses.KEY_DOWN, ord("j"), ord("J")):
            self.cursor = min(len(self.filtered) - 1, self.cursor + 1)
        elif key in (curses.KEY_PPAGE,):
            self.cursor = max(0, self.cursor - 10)
        elif key in (curses.KEY_NPAGE,):
            self.cursor = min(len(self.filtered) - 1, self.cursor + 10)
        elif key in (curses.KEY_HOME,):
            self.cursor = 0
        elif key in (curses.KEY_END,):
            self.cursor = max(0, len(self.filtered) - 1)
        elif key == 9:  # Tab
            self.genre_idx = (self.genre_idx + 1) % len(GENRE_ORDER)
            self._apply_filter()
        elif key in (curses.KEY_BTAB,):  # Shift+Tab
            self.genre_idx = (self.genre_idx - 1) % len(GENRE_ORDER)
            self._apply_filter()
        elif key in (10, 13, curses.KEY_ENTER, curses.KEY_RIGHT):
            if self.filtered:
                return "open"
        elif key == ord("/"):
            return "search"
        elif key in (ord("c"), ord("C")):
            return "collection"
        elif key in (ord("r"), ord("R")):
            return "random"
        elif key in (ord("f"), ord("F")):
            book = self.selected_book()
            if book:
                if book.title in self.favorites:
                    self.favorites.remove(book.title)
                else:
                    self.favorites.append(book.title)
                return "toggle_fav"
        elif key == ord("?"):
            return "help"

        return None

    def render(self, stdscr) -> None:
        h, w = stdscr.getmaxyx()
        stdscr.erase()

        # Title art
        start_y = 0
        for i, line in enumerate(TITLE_ART):
            if i >= h - 3:
                break
            draw_centered(
                stdscr, start_y + i, line,
                curses.color_pair(TITLE_HIGHLIGHT) | curses.A_BOLD,
            )

        # Genre tabs
        tab_y = start_y + len(TITLE_ART) + 1
        if tab_y < h - 2:
            tab_x = 2
            for i, genre in enumerate(GENRE_ORDER):
                icon = GENRE_ICONS.get(genre, "●")
                label = f" {icon} {genre.title()} "
                if i == self.genre_idx:
                    attr = curses.A_REVERSE | curses.A_BOLD
                    if genre in GENRE_COLORS:
                        attr |= curses.color_pair(GENRE_COLORS[genre])
                    else:
                        attr |= curses.color_pair(TITLE_HIGHLIGHT)
                else:
                    attr = curses.A_DIM
                    if genre in GENRE_COLORS:
                        attr |= curses.color_pair(GENRE_COLORS[genre])
                safe_addstr(stdscr, tab_y, tab_x, label, attr)
                tab_x += len(label) + 1

            # Book count
            count_text = f"  ({len(self.filtered)} books)"
            safe_addstr(stdscr, tab_y, tab_x, count_text, curses.A_DIM)

        # Separator
        sep_y = tab_y + 1
        if sep_y < h - 2:
            safe_addstr(
                stdscr, sep_y, 1, "─" * (w - 2),
                curses.color_pair(SHELF_FRAME) | curses.A_DIM,
            )

        # Book list
        list_start = sep_y + 1
        visible_rows = h - list_start - 2  # leave room for status bar

        if visible_rows <= 0:
            draw_status_bar(stdscr, "Terminal too small")
            return

        # Adjust scroll to keep cursor visible
        if self.cursor < self.scroll_offset:
            self.scroll_offset = self.cursor
        elif self.cursor >= self.scroll_offset + visible_rows:
            self.scroll_offset = self.cursor - visible_rows + 1

        for i in range(visible_rows):
            book_idx = self.scroll_offset + i
            if book_idx >= len(self.filtered):
                break

            book = self.filtered[book_idx]
            row_y = list_start + i
            is_selected = book_idx == self.cursor

            # Build the line
            genre_icon = GENRE_ICONS.get(book.genre, "●")
            fav = "♥" if book.title in self.favorites else " "
            title_part = truncate(book.title, 35)
            author_part = truncate(book.author, 25)
            year_part = str(book.year)

            # Compose line parts
            prefix = f"  {fav} {genre_icon} "
            line = f"{title_part:<36} {author_part:<26} {year_part}"

            if is_selected:
                # Highlight entire row
                full_line = (prefix + line).ljust(w - 1)
                safe_addstr(
                    stdscr, row_y, 0, full_line,
                    curses.A_REVERSE | curses.A_BOLD,
                )
            else:
                # Fav heart
                if fav == "♥":
                    safe_addstr(
                        stdscr, row_y, 2, "♥",
                        curses.color_pair(FAVORITE_HEART) | curses.A_BOLD,
                    )
                    safe_addstr(stdscr, row_y, 4, f"{genre_icon} ", curses.color_pair(
                        GENRE_COLORS.get(book.genre, BODY_TEXT)
                    ))
                else:
                    safe_addstr(stdscr, row_y, 2, f"  {genre_icon} ", curses.color_pair(
                        GENRE_COLORS.get(book.genre, BODY_TEXT)
                    ))

                safe_addstr(stdscr, row_y, 6, f"{title_part:<36}", curses.color_pair(BODY_TEXT))
                safe_addstr(
                    stdscr, row_y, 43, f"{author_part:<26}",
                    curses.color_pair(BODY_TEXT) | curses.A_DIM,
                )
                safe_addstr(stdscr, row_y, 70, year_part, curses.A_DIM)

        # Scroll indicator
        if len(self.filtered) > visible_rows:
            pos = f"[{self.cursor + 1}/{len(self.filtered)}]"
            safe_addstr(stdscr, list_start - 1, w - len(pos) - 2, pos, curses.A_DIM)

        # Status bar
        genre_name = self.current_genre.title()
        status = f" ↑↓ Navigate  Enter: Open  Tab: Genre ({genre_name})  /: Search  f: Fav  c: Collection  r: Random  ?: Help  q: Quit"
        draw_status_bar(stdscr, status)
