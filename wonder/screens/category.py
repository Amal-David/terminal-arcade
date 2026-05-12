"""Category picker screen — the main entry view for wonder."""

from __future__ import annotations

import curses
import datetime as _dt

from wonder.fetcher import (
    CATEGORIES,
    CATEGORY_ICONS,
    CATEGORY_LABELS,
    SURPRISE,
)
from wonder.ui.colors import (
    BODY_TEXT,
    CATEGORY_COLORS,
    FRAME,
    SAVED_HEART,
    TITLE_HIGHLIGHT,
)
from wonder.ui.widgets import draw_centered, draw_status_bar, safe_addstr

TITLE_ART = [
    "██╗    ██╗ ██████╗ ███╗   ██╗██████╗ ███████╗██████╗ ",
    "██║    ██║██╔═══██╗████╗  ██║██╔══██╗██╔════╝██╔══██╗",
    "██║ █╗ ██║██║   ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝",
    "██║███╗██║██║   ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗",
    "╚███╔███╔╝╚██████╔╝██║ ╚████║██████╔╝███████╗██║  ██║",
    " ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝",
]

OPTIONS = [*CATEGORIES, SURPRISE]

DESCRIPTIONS = {
    "funny": "Dad jokes and the silly side of the internet.",
    "heartwarming": "Uplifting news and small acts of kindness from today.",
    "weird": "A strange-but-true fact you didn't know you needed.",
    "inspiring": "A story to remind you what people are capable of.",
    SURPRISE: "Let the day pick. One of the four, at random.",
}


class CategoryScreen:
    """Picker screen for the four moods + surprise me."""

    def __init__(self, day_status: dict[str, str], favorites_count: int = 0) -> None:
        self.cursor = 0
        self.day_status = day_status  # category -> "cached" | "offline" | None
        self.favorites_count = favorites_count

    def selected_category(self) -> str:
        return OPTIONS[self.cursor]

    def handle_input(self, key: int) -> str | None:
        if key in (ord("q"), ord("Q"), 27):
            return "quit"
        if key in (curses.KEY_UP, ord("k"), ord("K")):
            self.cursor = (self.cursor - 1) % len(OPTIONS)
            return None
        if key in (curses.KEY_DOWN, ord("j"), ord("J")):
            self.cursor = (self.cursor + 1) % len(OPTIONS)
            return None
        if key in (10, 13, curses.KEY_ENTER, curses.KEY_RIGHT, ord(" ")):
            return "open"
        if key in (ord("f"), ord("F")):
            return "favorites"
        if key == ord("?"):
            return "help"
        if ord("1") <= key <= ord("5"):
            idx = key - ord("1")
            if idx < len(OPTIONS):
                self.cursor = idx
                return "open"
        return None

    def render(self, stdscr) -> None:
        h, w = stdscr.getmaxyx()
        stdscr.erase()

        # Title art
        for i, line in enumerate(TITLE_ART):
            if i + 1 >= h - 4:
                break
            draw_centered(
                stdscr,
                1 + i,
                line,
                curses.color_pair(TITLE_HIGHLIGHT) | curses.A_BOLD,
            )

        sub_y = 1 + len(TITLE_ART) + 1
        today = _dt.date.today().strftime("%A, %B %d, %Y")
        draw_centered(
            stdscr,
            sub_y,
            f"your daily curiosity — {today}",
            curses.color_pair(FRAME),
        )

        # Options list
        list_top = sub_y + 2
        for i, option in enumerate(OPTIONS):
            row_y = list_top + i * 2
            if row_y >= h - 2:
                break
            label = CATEGORY_LABELS.get(option, option.title())
            icon = CATEGORY_ICONS.get(option, "•")
            status = self.day_status.get(option)
            status_text = ""
            status_attr = curses.A_DIM
            if status == "cached":
                status_text = " · today's pick saved"
                status_attr = curses.color_pair(FRAME)
            elif status == "offline":
                status_text = " · offline pick"
                status_attr = curses.color_pair(SAVED_HEART)
            elif status is None and option != SURPRISE:
                status_text = " · ready to fetch"
                status_attr = curses.A_DIM

            color_pair = CATEGORY_COLORS.get(option, BODY_TEXT)
            is_selected = i == self.cursor

            prefix = "▶ " if is_selected else "  "
            line = f"{prefix}[{i + 1}] {icon}  {label}"

            if is_selected:
                attr = curses.A_REVERSE | curses.A_BOLD | curses.color_pair(color_pair)
                full = (line + status_text).ljust(w - 4)
                safe_addstr(stdscr, row_y, 4, full, attr)
            else:
                safe_addstr(stdscr, row_y, 4, line, curses.color_pair(color_pair) | curses.A_BOLD)
                if status_text:
                    safe_addstr(stdscr, row_y, 4 + len(line), status_text, status_attr)

            # Description on next row
            desc = DESCRIPTIONS.get(option, "")
            safe_addstr(stdscr, row_y + 1, 10, desc, curses.A_DIM)

        # Favorites hint
        fav_y = list_top + len(OPTIONS) * 2 + 1
        if fav_y < h - 2 and self.favorites_count > 0:
            text = f"  ♥ {self.favorites_count} saved — press F to revisit"
            safe_addstr(stdscr, fav_y, 4, text, curses.color_pair(SAVED_HEART) | curses.A_BOLD)

        status = " ↑↓ pick   Enter open   1-5 quick   F favorites   ? help   Q back "
        draw_status_bar(stdscr, status)
