"""Main bookshelf application — curses entry point and screen manager."""

from __future__ import annotations

import curses
import sys

from bookshelf.data.books import Book, load_all_books
from bookshelf.data.quotes import QUOTES
from bookshelf.screens.book_detail import BookDetailScreen
from bookshelf.screens.collection import CollectionScreen
from bookshelf.screens.search import SearchScreen
from bookshelf.screens.shelf import ShelfScreen
from bookshelf.storage import (
    increment_stats,
    load_state,
    mark_read,
    mark_want_to_read,
    save_state,
    toggle_favorite,
)
from bookshelf.ui.colors import init_colors
from bookshelf.ui.widgets import draw_help_overlay

MIN_WIDTH = 80
MIN_HEIGHT = 24

HELP_BINDINGS = [
    ("↑/↓ j/k", "Navigate books"),
    ("Enter/→", "Open book"),
    ("Esc/← q", "Back / Quit"),
    ("Tab", "Cycle genre filter"),
    ("/", "Search books"),
    ("f", "Toggle favorite"),
    ("c", "My collection"),
    ("r", "Random book"),
    ("←/→ n/p", "Browse quotes (detail)"),
    ("m", "Mark as read (detail)"),
    ("w", "Want to read (detail)"),
    ("PgUp/PgDn", "Scroll fast"),
    ("?", "This help"),
]


def _quotes_for_book(book: Book) -> list:
    """Get quotes matching a book title."""
    return [q for q in QUOTES if q.book_title == book.title]


def main(stdscr) -> None:
    # Setup
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(50)  # 20 FPS
    init_colors()

    # Load data
    all_books = load_all_books()
    state = load_state()
    favorites = list(state.get("favorites", []))
    read_list = list(state.get("read", []))
    want_list = list(state.get("want_to_read", []))

    # Screen stack
    shelf = ShelfScreen(all_books, favorites)
    screen_stack: list = [shelf]
    show_help = False

    while True:
        h, w = stdscr.getmaxyx()

        # Size check
        if h < MIN_HEIGHT or w < MIN_WIDTH:
            stdscr.erase()
            msg = f"Terminal too small ({w}x{h}). Need {MIN_WIDTH}x{MIN_HEIGHT}."
            try:
                stdscr.addstr(h // 2, max(0, (w - len(msg)) // 2), msg)
            except curses.error:
                pass
            stdscr.refresh()
            key = stdscr.getch()
            if key in (ord("q"), ord("Q"), 27):
                break
            continue

        current = screen_stack[-1]

        # Render
        current.render(stdscr)

        if show_help:
            draw_help_overlay(stdscr, HELP_BINDINGS)

        stdscr.refresh()

        # Input
        key = stdscr.getch()
        if key == -1:
            continue

        # Help toggle
        if show_help:
            show_help = False
            continue

        # Dispatch to current screen
        if isinstance(current, ShelfScreen):
            action = current.handle_input(key)

            if action == "quit":
                break
            elif action == "open":
                book = current.selected_book()
                if book:
                    quotes = _quotes_for_book(book)
                    detail = BookDetailScreen(book, quotes, favorites)
                    screen_stack.append(detail)
                    increment_stats(books_explored=1)
            elif action == "search":
                search = SearchScreen(all_books)
                screen_stack.append(search)
            elif action == "collection":
                stats = load_state()
                coll = CollectionScreen(
                    all_books, favorites, read_list, want_list, stats
                )
                screen_stack.append(coll)
            elif action == "random":
                book = current.random_book()
                if book:
                    quotes = _quotes_for_book(book)
                    detail = BookDetailScreen(book, quotes, favorites)
                    screen_stack.append(detail)
                    increment_stats(books_explored=1)
            elif action == "toggle_fav":
                _sync_favorites(favorites)
            elif action == "help":
                show_help = True

        elif isinstance(current, BookDetailScreen):
            action = current.handle_input(key)

            if action == "back":
                screen_stack.pop()
            elif action == "toggle_fav":
                _sync_favorites(favorites)
            elif action == "mark_read":
                mark_read(current.book.title)
                if current.book.title not in read_list:
                    read_list.append(current.book.title)
                if current.book.title in want_list:
                    want_list.remove(current.book.title)
            elif action == "mark_want":
                mark_want_to_read(current.book.title)
                if current.book.title not in want_list:
                    want_list.append(current.book.title)
            # Track quote views
            if action is None and key in (curses.KEY_RIGHT, ord("n"), ord("N")):
                increment_stats(quotes_seen=1)

        elif isinstance(current, SearchScreen):
            action = current.handle_input(key)

            if action == "back":
                screen_stack.pop()
            elif action == "open":
                book = current.selected_book()
                if book:
                    quotes = _quotes_for_book(book)
                    detail = BookDetailScreen(book, quotes, favorites)
                    screen_stack.append(detail)
                    increment_stats(books_explored=1)

        elif isinstance(current, CollectionScreen):
            action = current.handle_input(key)

            if action == "back":
                screen_stack.pop()
            elif action == "open":
                book = current.selected_book()
                if book:
                    quotes = _quotes_for_book(book)
                    detail = BookDetailScreen(book, quotes, favorites)
                    screen_stack.append(detail)
                    increment_stats(books_explored=1)

    # Save state on exit
    _sync_favorites(favorites)


def _sync_favorites(favorites: list[str]) -> None:
    """Persist favorites to disk."""
    state = load_state()
    state["favorites"] = list(favorites)
    save_state(state)


def run() -> None:
    """Entry point for the bookshelf app."""
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()
