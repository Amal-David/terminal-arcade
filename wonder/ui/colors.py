"""Color pair definitions for the wonder TUI."""

import curses

FRAME = 1
TITLE_HIGHLIGHT = 2
BODY_TEXT = 3
CAT_FUNNY = 4
CAT_HEART = 5
CAT_WEIRD = 6
CAT_INSPIRE = 7
SAVED_HEART = 8
ORIGIN_LIVE = 9
ORIGIN_OFFLINE = 10

CATEGORY_COLORS = {
    "funny": CAT_FUNNY,
    "heartwarming": CAT_HEART,
    "weird": CAT_WEIRD,
    "inspiring": CAT_INSPIRE,
}


def init_colors() -> None:
    """Initialize curses color pairs."""
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(FRAME, curses.COLOR_CYAN, -1)
    curses.init_pair(TITLE_HIGHLIGHT, curses.COLOR_YELLOW, -1)
    curses.init_pair(BODY_TEXT, curses.COLOR_WHITE, -1)
    curses.init_pair(CAT_FUNNY, curses.COLOR_YELLOW, -1)
    curses.init_pair(CAT_HEART, curses.COLOR_MAGENTA, -1)
    curses.init_pair(CAT_WEIRD, curses.COLOR_CYAN, -1)
    curses.init_pair(CAT_INSPIRE, curses.COLOR_GREEN, -1)
    curses.init_pair(SAVED_HEART, curses.COLOR_RED, -1)
    curses.init_pair(ORIGIN_LIVE, curses.COLOR_GREEN, -1)
    curses.init_pair(ORIGIN_OFFLINE, curses.COLOR_YELLOW, -1)
