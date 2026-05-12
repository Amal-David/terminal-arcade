"""Favorites screen — list of saved stories."""

from __future__ import annotations

import curses

from wonder.fetcher import CATEGORY_ICONS, CATEGORY_LABELS
from wonder.ui.colors import (
    BODY_TEXT,
    CATEGORY_COLORS,
    FRAME,
    SAVED_HEART,
    TITLE_HIGHLIGHT,
)
from wonder.ui.widgets import draw_status_bar, safe_addstr, truncate


class FavoritesScreen:
    """List of saved stories with re-open and remove."""

    def __init__(self, favorites: list[dict]) -> None:
        self.favorites = favorites
        self.cursor = 0
        self.scroll = 0

    def selected(self) -> dict | None:
        if 0 <= self.cursor < len(self.favorites):
            return self.favorites[self.cursor]
        return None

    def handle_input(self, key: int) -> str | None:
        if key in (ord("q"), ord("Q"), 27, curses.KEY_LEFT):
            return "back"
        if not self.favorites:
            return None
        if key in (curses.KEY_UP, ord("k"), ord("K")):
            self.cursor = max(0, self.cursor - 1)
        elif key in (curses.KEY_DOWN, ord("j"), ord("J")):
            self.cursor = min(len(self.favorites) - 1, self.cursor + 1)
        elif key in (10, 13, curses.KEY_ENTER, curses.KEY_RIGHT):
            return "open"
        elif key in (ord("d"), ord("D")):
            return "remove"
        elif key == ord("?"):
            return "help"
        return None

    def render(self, stdscr) -> None:
        h, w = stdscr.getmaxyx()
        stdscr.erase()

        header = "  ♥  Saved Wonders  "
        safe_addstr(stdscr, 1, 2, header, curses.color_pair(SAVED_HEART) | curses.A_REVERSE | curses.A_BOLD)
        safe_addstr(stdscr, 2, 1, "─" * (w - 2), curses.color_pair(FRAME) | curses.A_DIM)

        if not self.favorites:
            empty = "Nothing saved yet — press S on a story to save it for later."
            safe_addstr(stdscr, h // 2, max(0, (w - len(empty)) // 2), empty, curses.A_DIM)
            draw_status_bar(stdscr, " ←/Esc back ")
            return

        list_top = 4
        visible_rows = max(1, h - list_top - 3)
        if self.cursor < self.scroll:
            self.scroll = self.cursor
        elif self.cursor >= self.scroll + visible_rows:
            self.scroll = self.cursor - visible_rows + 1

        for i in range(visible_rows):
            idx = self.scroll + i
            if idx >= len(self.favorites):
                break
            fav = self.favorites[idx]
            row_y = list_top + i
            category = fav.get("category", "")
            icon = CATEGORY_ICONS.get(category, "•")
            label = CATEGORY_LABELS.get(category, category.title())
            date = fav.get("fetched_at", "")
            title = fav.get("title", "Wonder")
            body_preview = (fav.get("body") or "").replace("\n", " ")
            color = CATEGORY_COLORS.get(category, BODY_TEXT)

            prefix = "▶ " if idx == self.cursor else "  "
            head = f"{prefix}{icon} {label:<14} {date:<10}"
            tail = f"  {truncate(title, 32)}  —  {truncate(body_preview, max(10, w - 70))}"

            if idx == self.cursor:
                attr = curses.color_pair(color) | curses.A_REVERSE | curses.A_BOLD
                safe_addstr(stdscr, row_y, 2, (head + tail).ljust(w - 4), attr)
            else:
                safe_addstr(stdscr, row_y, 2, head, curses.color_pair(color) | curses.A_BOLD)
                safe_addstr(stdscr, row_y, 2 + len(head), tail, curses.color_pair(BODY_TEXT))

        if len(self.favorites) > visible_rows:
            pos = f"[{self.cursor + 1}/{len(self.favorites)}]"
            safe_addstr(stdscr, list_top - 1, w - len(pos) - 2, pos, curses.A_DIM)

        status = " ↑↓ pick   Enter open   D remove   ←/Esc back   ? help "
        draw_status_bar(stdscr, status)
