"""Story screen — fetches and renders a single Story for a category."""

from __future__ import annotations

import curses
import threading
import time

from wonder.fetcher import (
    CATEGORY_ICONS,
    CATEGORY_LABELS,
    SURPRISE,
    fetch_story,
)
from wonder.storage import is_favorite
from wonder.ui.colors import (
    BODY_TEXT,
    CATEGORY_COLORS,
    FRAME,
    ORIGIN_LIVE,
    ORIGIN_OFFLINE,
    SAVED_HEART,
    TITLE_HIGHLIGHT,
)
from wonder.ui.widgets import (
    draw_centered,
    draw_status_bar,
    safe_addstr,
    wrap_text,
)

LOADING_FRAMES = [
    "Looking for something wonderful   ",
    "Looking for something wonderful.  ",
    "Looking for something wonderful.. ",
    "Looking for something wonderful...",
]


class StoryScreen:
    """Renders one story. Fetches in a background thread to keep UI live."""

    def __init__(self, category: str, favorites: list[dict], readonly_story: dict | None = None) -> None:
        self.category = category
        self.favorites = favorites
        self.story: dict | None = readonly_story
        self.error: str | None = None
        self.fetching = readonly_story is None
        self.readonly = readonly_story is not None
        self._loading_tick = 0
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._scroll = 0

        if self.fetching:
            self._start_fetch(force_refresh=False)

    def _start_fetch(self, *, force_refresh: bool) -> None:
        self.fetching = True
        self.error = None
        if not force_refresh:
            self.story = None

        def worker():
            try:
                story = fetch_story(self.category, force_refresh=force_refresh)
                with self._lock:
                    self.story = story
                    self.fetching = False
            except Exception as exc:  # noqa: BLE001 — last-resort UI guard
                with self._lock:
                    self.error = f"Could not load: {exc}"
                    self.fetching = False

        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()

    def is_favorite(self) -> bool:
        if not self.story:
            return False
        return is_favorite(self.story, self.favorites)

    def handle_input(self, key: int) -> str | None:
        if key in (ord("q"), ord("Q"), 27, curses.KEY_LEFT):
            return "back"
        if not self.fetching and self.story is not None:
            if key in (ord("r"), ord("R")) and not self.readonly:
                self._start_fetch(force_refresh=True)
                self._scroll = 0
                return None
            if key in (ord("s"), ord("S")):
                return "toggle_save"
            if key in (curses.KEY_DOWN, ord("j"), ord("J")):
                self._scroll += 1
                return None
            if key in (curses.KEY_UP, ord("k"), ord("K")):
                self._scroll = max(0, self._scroll - 1)
                return None
            if key == curses.KEY_NPAGE:
                self._scroll += 5
                return None
            if key == curses.KEY_PPAGE:
                self._scroll = max(0, self._scroll - 5)
                return None
        if key == ord("?"):
            return "help"
        return None

    def tick(self) -> None:
        """Called from the main loop to advance the loading animation."""
        if self.fetching:
            self._loading_tick = (self._loading_tick + 1) % (len(LOADING_FRAMES) * 4)

    def render(self, stdscr) -> None:
        h, w = stdscr.getmaxyx()
        stdscr.erase()

        category = self.category
        label = CATEGORY_LABELS.get(category, category.title())
        icon = CATEGORY_ICONS.get(category, "•")
        color_pair = CATEGORY_COLORS.get(category, BODY_TEXT)

        header = f"  {icon}  {label}  "
        safe_addstr(stdscr, 1, 2, header, curses.color_pair(color_pair) | curses.A_BOLD | curses.A_REVERSE)

        # Separator
        safe_addstr(stdscr, 2, 1, "─" * (w - 2), curses.color_pair(FRAME) | curses.A_DIM)

        if self.fetching:
            frame = LOADING_FRAMES[self._loading_tick // 4 % len(LOADING_FRAMES)]
            draw_centered(stdscr, h // 2, frame, curses.color_pair(FRAME) | curses.A_BOLD)
            safe_addstr(
                stdscr, h // 2 + 2, 0,
                "(if the network is slow, an offline pick will appear shortly)".center(w),
                curses.A_DIM,
            )
        elif self.error:
            draw_centered(stdscr, h // 2, self.error, curses.color_pair(SAVED_HEART) | curses.A_BOLD)
        elif self.story:
            self._render_story(stdscr, h, w)

        if self.readonly:
            footer = " ↑↓ scroll   ←/Esc back   ? help "
        elif self.fetching:
            footer = " ←/Esc back   Q quit "
        else:
            saved = "♥ saved" if self.is_favorite() else "♡ save"
            footer = f" ↑↓ scroll   R refresh   S {saved}   ←/Esc back   ? help "
        draw_status_bar(stdscr, footer)

    def _render_story(self, stdscr, h: int, w: int) -> None:
        story = self.story or {}
        title = story.get("title") or "Wonder"
        body = story.get("body") or ""
        source = story.get("source") or ""
        url = story.get("url") or ""
        origin = story.get("origin") or "live"

        text_left = 4
        text_right = max(text_left + 1, w - 4)
        text_width = text_right - text_left

        # Title
        title_y = 4
        safe_addstr(
            stdscr, title_y, text_left, title,
            curses.color_pair(TITLE_HIGHLIGHT) | curses.A_BOLD,
        )

        # Saved indicator
        if self.is_favorite():
            fav_label = " ♥ saved "
            safe_addstr(
                stdscr, title_y, max(text_left, w - len(fav_label) - 4),
                fav_label, curses.color_pair(SAVED_HEART) | curses.A_BOLD,
            )

        # Body
        body_y = title_y + 2
        body_lines = wrap_text(body, text_width)
        max_lines = max(0, h - body_y - 4)
        if self._scroll > max(0, len(body_lines) - max_lines):
            self._scroll = max(0, len(body_lines) - max_lines)
        visible = body_lines[self._scroll:self._scroll + max_lines]
        for i, line in enumerate(visible):
            safe_addstr(stdscr, body_y + i, text_left, line, curses.color_pair(BODY_TEXT))

        # Scroll hint
        if len(body_lines) > max_lines:
            hint = f"[{self._scroll + 1}-{min(len(body_lines), self._scroll + max_lines)}/{len(body_lines)}]"
            safe_addstr(stdscr, body_y - 1, text_right - len(hint), hint, curses.A_DIM)

        # Source / origin footer
        origin_label, origin_color = {
            "live": ("today's fresh pick", ORIGIN_LIVE),
            "cache": ("today's pick (cached)", FRAME),
            "fallback": ("offline pick", ORIGIN_OFFLINE),
        }.get(origin, ("today's pick", FRAME))

        src_y = h - 3
        src_text = f"Source: {source}" if source else "Source: —"
        safe_addstr(stdscr, src_y, text_left, src_text, curses.color_pair(FRAME))
        safe_addstr(
            stdscr, src_y, max(text_left + len(src_text) + 2, text_right - len(origin_label) - 2),
            f"({origin_label})", curses.color_pair(origin_color) | curses.A_BOLD,
        )
        if url:
            safe_addstr(stdscr, src_y + 1, text_left, url, curses.A_DIM)
