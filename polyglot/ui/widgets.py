"""Drawing helpers reused across polyglot screens."""

from __future__ import annotations

import curses


def safe_addstr(stdscr, y: int, x: int, text: str, attr: int = 0) -> None:
    """Draw text while clipping to visible terminal bounds."""
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
        stdscr.addstr(y, x, text, attr)
    except curses.error:
        pass


def draw_box(stdscr, y: int, x: int, width: int, height: int, attr: int = 0) -> None:
    if width < 2 or height < 2:
        return
    safe_addstr(stdscr, y, x, "╔" + "═" * (width - 2) + "╗", attr)
    for row in range(1, height - 1):
        safe_addstr(stdscr, y + row, x, "║", attr)
        safe_addstr(stdscr, y + row, x + width - 1, "║", attr)
    safe_addstr(stdscr, y + height - 1, x, "╚" + "═" * (width - 2) + "╝", attr)


def init_colors() -> bool:
    if not curses.has_colors():
        return False
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_YELLOW, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_WHITE, -1)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)
    return True


def display_width(text: str) -> int:
    """Approximate display width — most CJK glyphs are wide; rest are narrow.

    Used for grid alignment. Far from perfect but good enough for the cabinet UI.
    """
    width = 0
    for ch in text:
        cp = ord(ch)
        if (
            0x1100 <= cp <= 0x115F  # Hangul Jamo
            or 0x2E80 <= cp <= 0x303E  # CJK radicals + punctuation
            or 0x3041 <= cp <= 0x33FF  # Hiragana, Katakana, CJK symbols
            or 0x3400 <= cp <= 0x4DBF  # CJK ext A
            or 0x4E00 <= cp <= 0x9FFF  # CJK unified
            or 0xA000 <= cp <= 0xA4CF  # Yi
            or 0xAC00 <= cp <= 0xD7A3  # Hangul syllables
            or 0xF900 <= cp <= 0xFAFF  # CJK compat
            or 0xFE30 <= cp <= 0xFE4F  # CJK compat forms
            or 0xFF00 <= cp <= 0xFF60  # fullwidth forms
            or 0xFFE0 <= cp <= 0xFFE6
            or 0x1F300 <= cp <= 0x1FAFF  # emoji ranges
        ):
            width += 2
        elif cp < 0x20 or cp == 0x7F:
            continue
        else:
            width += 1
    return width
