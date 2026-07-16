"""Shared defensive curses operations."""

from __future__ import annotations

import curses


def safe_addstr(stdscr, y: int, x: int, text: str, attr: int = 0) -> None:
    """Draw clipped text without failing on a terminal edge."""
    height, width = stdscr.getmaxyx()
    if y < 0 or y >= height or x >= width:
        return
    if x < 0:
        text = text[-x:]
        x = 0
    max_len = width - x - 1
    if max_len <= 0:
        return
    text = text[:max_len]
    try:
        addnstr = getattr(stdscr, "addnstr", None)
        if addnstr is not None:
            addnstr(y, x, text, max_len, attr)
        else:
            stdscr.addstr(y, x, text, attr)
    except (curses.error, OSError):
        pass


def hide_cursor() -> None:
    """Hide the cursor when supported by the active terminal."""
    try:
        curses.curs_set(0)
    except (curses.error, OSError):
        pass


def show_cursor() -> None:
    """Restore the cursor when supported by the active terminal."""
    try:
        curses.curs_set(1)
    except (curses.error, OSError):
        pass
