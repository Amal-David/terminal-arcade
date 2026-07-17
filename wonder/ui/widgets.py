"""Reusable curses widgets for the wonder TUI."""

from __future__ import annotations

import curses

from terminal_arcade.ui import safe_addstr
from wonder.ui.colors import FRAME, TITLE_HIGHLIGHT


def truncate(text: str, max_len: int) -> str:
    if max_len <= 0:
        return ""
    if len(text) <= max_len:
        return text
    if max_len <= 1:
        return text[:max_len]
    return text[: max_len - 1] + "…"


def draw_box(stdscr, y: int, x: int, height: int, width: int, attr: int = 0) -> None:
    h, w = stdscr.getmaxyx()
    if y >= h or x >= w or width < 2 or height < 2:
        return
    top = "╔" + "═" * (width - 2) + "╗"
    bot = "╚" + "═" * (width - 2) + "╝"
    safe_addstr(stdscr, y, x, top, attr)
    for row in range(1, height - 1):
        safe_addstr(stdscr, y + row, x, "║", attr)
        safe_addstr(stdscr, y + row, x + width - 1, "║", attr)
    safe_addstr(stdscr, y + height - 1, x, bot, attr)


def draw_centered(stdscr, y: int, text: str, attr: int = 0) -> None:
    _, w = stdscr.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    safe_addstr(stdscr, y, x, text, attr)


def draw_status_bar(stdscr, text: str, attr: int = 0) -> None:
    h, w = stdscr.getmaxyx()
    bar = " " + truncate(text, w - 2)
    bar = bar.ljust(w - 1)
    safe_addstr(stdscr, h - 1, 0, bar, attr | curses.A_REVERSE)


def wrap_text(text: str, width: int) -> list[str]:
    """Soft-wrap text to a max width, preserving paragraph breaks."""
    if width <= 0:
        return []
    out: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            out.append("")
            continue
        words = paragraph.split()
        line = ""
        for word in words:
            if not line:
                line = word
            elif len(line) + 1 + len(word) <= width:
                line = line + " " + word
            else:
                out.append(line)
                line = word
        if line:
            out.append(line)
    return out


def draw_help_overlay(stdscr, bindings: list[tuple[str, str]]) -> None:
    h, w = stdscr.getmaxyx()
    box_w = min(50, w - 4)
    box_h = min(len(bindings) + 4, h - 4)
    start_y = max(0, (h - box_h) // 2)
    start_x = max(0, (w - box_w) // 2)

    draw_box(stdscr, start_y, start_x, box_h, box_w, curses.color_pair(FRAME))

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
        line = f"  {key:<14} {desc}"
        safe_addstr(stdscr, start_y + 2 + i, start_x + 2, truncate(line, box_w - 4))
