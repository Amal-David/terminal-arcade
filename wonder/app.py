"""Main wonder application — curses entry point and screen manager."""

from __future__ import annotations

import curses
import datetime as _dt

from wonder.fetcher import CATEGORIES, SURPRISE
from wonder.screens.category import CategoryScreen
from wonder.screens.favorites import FavoritesScreen
from wonder.screens.story import StoryScreen
from wonder.storage import (
    increment_stories_seen,
    load_cache,
    load_state,
    remove_favorite_at,
    save_state,
    toggle_favorite,
)
from wonder.ui.colors import init_colors
from wonder.ui.widgets import draw_help_overlay

MIN_WIDTH = 80
MIN_HEIGHT = 24

HELP_BINDINGS = [
    ("↑/↓ j/k", "Move cursor"),
    ("Enter/→", "Open"),
    ("Esc/← q", "Back / Quit"),
    ("R", "Refresh today's pick"),
    ("S", "Save / unsave"),
    ("F", "Open favorites"),
    ("D", "Delete favorite"),
    ("PgUp/PgDn", "Scroll body"),
    ("?", "This help"),
]


def _today_status(cache: dict) -> dict[str, str]:
    today = _dt.date.today().isoformat()
    day = cache.get(today, {}) if isinstance(cache, dict) else {}
    out: dict[str, str] = {}
    for category in CATEGORIES:
        story = day.get(category)
        if not isinstance(story, dict):
            continue
        if story.get("origin") == "fallback":
            out[category] = "offline"
        else:
            out[category] = "cached"
    return out


def main(stdscr) -> None:
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.nodelay(True)
    stdscr.timeout(120)
    init_colors()

    state = load_state()
    favorites = list(state.get("favorites", []))

    cache = load_cache()
    category_screen = CategoryScreen(_today_status(cache), len(favorites))
    screen_stack: list = [category_screen]
    show_help = False

    while True:
        h, w = stdscr.getmaxyx()

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
        if isinstance(current, StoryScreen):
            current.tick()

        current.render(stdscr)

        if show_help:
            draw_help_overlay(stdscr, HELP_BINDINGS)

        stdscr.refresh()

        key = stdscr.getch()
        if key == -1:
            continue

        if show_help:
            show_help = False
            continue

        if isinstance(current, CategoryScreen):
            action = current.handle_input(key)
            if action == "quit":
                break
            elif action == "open":
                category = current.selected_category()
                story_screen = StoryScreen(category, favorites)
                screen_stack.append(story_screen)
                increment_stories_seen()
            elif action == "favorites":
                screen_stack.append(FavoritesScreen(favorites))
            elif action == "help":
                show_help = True

        elif isinstance(current, StoryScreen):
            action = current.handle_input(key)
            if action == "back":
                screen_stack.pop()
                # Refresh category status when returning
                cache = load_cache()
                category_screen.day_status = _today_status(cache)
                category_screen.favorites_count = len(favorites)
            elif action == "toggle_save":
                if current.story:
                    toggle_favorite(current.story)
                    state = load_state()
                    favorites[:] = list(state.get("favorites", []))
                    current.favorites = favorites
            elif action == "help":
                show_help = True

        elif isinstance(current, FavoritesScreen):
            action = current.handle_input(key)
            if action == "back":
                screen_stack.pop()
                category_screen.favorites_count = len(favorites)
            elif action == "open":
                fav = current.selected()
                if fav:
                    story_screen = StoryScreen(
                        fav.get("category", SURPRISE),
                        favorites,
                        readonly_story=dict(fav),
                    )
                    screen_stack.append(story_screen)
            elif action == "remove":
                if 0 <= current.cursor < len(favorites):
                    remove_favorite_at(current.cursor)
                    state = load_state()
                    favorites[:] = list(state.get("favorites", []))
                    current.favorites = favorites
                    if current.cursor >= len(favorites):
                        current.cursor = max(0, len(favorites) - 1)
            elif action == "help":
                show_help = True

    # Persist any in-memory state on exit
    state = load_state()
    state["favorites"] = list(favorites)
    save_state(state)


def run() -> None:
    """Entry point for the wonder app."""
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()
