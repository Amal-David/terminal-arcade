"""Reusable curses widgets for the bookshelf TUI."""

from __future__ import annotations

import curses
from bookshelf.ui.colors import (
    BODY_TEXT,
    FAVORITE_HEART,
    GENRE_COLORS,
    MOOD_TAG,
    SHELF_FRAME,
    TITLE_HIGHLIGHT,
)
from bookshelf.ui.ascii_art import truncate


def safe_addstr(stdscr, y: int, x: int, text: str, attr: int = 0) -> None:
    """Write text to screen with bounds checking."""
    h, w = stdscr.getmaxyx()
    if y < 0 or y >= h or x >= w:
        return
    if x < 0:
        text = text[-x:]
        x = 0
    max_len = w - x - 1
    if max_len <= 0:
        return
    try:
        stdscr.addnstr(y, x, text, max_len, attr)
    except curses.error:
        pass


def draw_box(stdscr, y: int, x: int, height: int, width: int, attr: int = 0) -> None:
    """Draw a box outline."""
    h, w = stdscr.getmaxyx()
    if y >= h or x >= w:
        return

    top = "╔" + "═" * (width - 2) + "╗"
    bot = "╚" + "═" * (width - 2) + "╝"
    mid = "║" + " " * (width - 2) + "║"

    safe_addstr(stdscr, y, x, top, attr)
    for row in range(1, height - 1):
        safe_addstr(stdscr, y + row, x, mid, attr)
    safe_addstr(stdscr, y + height - 1, x, bot, attr)


def draw_status_bar(stdscr, text: str, attr: int = 0) -> None:
    """Draw a status bar at the bottom of the screen."""
    h, w = stdscr.getmaxyx()
    bar = " " + truncate(text, w - 2)
    bar = bar.ljust(w - 1)
    safe_addstr(stdscr, h - 1, 0, bar, attr | curses.A_REVERSE)


def draw_centered(stdscr, y: int, text: str, attr: int = 0) -> None:
    """Draw text centered horizontally."""
    _, w = stdscr.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    safe_addstr(stdscr, y, x, text, attr)


def draw_scroll_indicator(stdscr, y: int, x: int, current: int, total: int) -> None:
    """Draw a scroll position indicator like [3/10]."""
    if total <= 0:
        return
    text = f"[{current + 1}/{total}]"
    safe_addstr(stdscr, y, x, text, curses.color_pair(SHELF_FRAME))


def draw_genre_badge(stdscr, y: int, x: int, genre: str) -> None:
    """Draw a colored genre badge."""
    from bookshelf.ui.ascii_art import GENRE_ICONS

    icon = GENRE_ICONS.get(genre, "●")
    color = GENRE_COLORS.get(genre, BODY_TEXT)
    label = f" {icon} {genre.title()} "
    safe_addstr(stdscr, y, x, label, curses.color_pair(color) | curses.A_BOLD)


def draw_mood_tags(stdscr, y: int, x: int, moods: list[str], max_width: int) -> None:
    """Draw mood tags in a row."""
    col = x
    for mood in moods:
        tag = f" {mood} "
        if col + len(tag) + 1 > x + max_width:
            break
        safe_addstr(stdscr, y, col, tag, curses.color_pair(MOOD_TAG) | curses.A_DIM)
        col += len(tag) + 1


def draw_heart(stdscr, y: int, x: int, filled: bool) -> None:
    """Draw a heart icon (filled or empty)."""
    char = "♥" if filled else "♡"
    attr = curses.color_pair(FAVORITE_HEART) | curses.A_BOLD if filled else 0
    safe_addstr(stdscr, y, x, char, attr)


def draw_progress_bar(
    stdscr, y: int, x: int, width: int, fraction: float, attr: int = 0
) -> None:
    """Draw a simple progress bar."""
    filled = int(fraction * (width - 2))
    empty = width - 2 - filled
    bar = "[" + "█" * filled + "░" * empty + "]"
    safe_addstr(stdscr, y, x, bar, attr)


def draw_help_overlay(stdscr, bindings: list[tuple[str, str]]) -> None:
    """Draw a centered help overlay with key bindings."""
    h, w = stdscr.getmaxyx()
    box_w = min(50, w - 4)
    box_h = min(len(bindings) + 4, h - 4)
    start_y = max(0, (h - box_h) // 2)
    start_x = max(0, (w - box_w) // 2)

    draw_box(
        stdscr, start_y, start_x, box_h, box_w, curses.color_pair(SHELF_FRAME)
    )

    title = " Help "
    safe_addstr(
        stdscr,
        start_y,
        start_x + (box_w - len(title)) // 2,
        title,
        curses.color_pair(TITLE_HIGHLIGHT) | curses.A_BOLD,
    )

    for i, (key, desc) in enumerate(bindings):
        if i >= box_h - 3:
            break
        line = f"  {key:<12} {desc}"
        safe_addstr(
            stdscr,
            start_y + 2 + i,
            start_x + 2,
            truncate(line, box_w - 4),
        )
