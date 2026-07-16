"""Retro launcher for the terminal arcade collection."""

from __future__ import annotations

import curses
import textwrap
from dataclasses import dataclass
from typing import Callable

from terminal_arcade.catalog import (
    AMBIENT_CATEGORY,
    BOOK_COUNT,
    CATEGORY_LABELS,
    GAME_CATEGORY,
    POLYGLOT_PAIR_COUNT,
)
from terminal_arcade.ui import hide_cursor, safe_addstr

MIN_WIDTH = 80
MIN_HEIGHT = 28

MOVE_UP_KEYS = {curses.KEY_UP, ord("k"), ord("K")}
MOVE_DOWN_KEYS = {curses.KEY_DOWN, ord("j"), ord("J")}
LAUNCH_KEYS = {curses.KEY_ENTER, 10, 13, ord(" ")}
QUIT_KEYS = {ord("q"), ord("Q"), 27}

TITLE_ART = [
    "  █████╗ ██████╗  ██████╗ █████╗ ██████╗ ███████╗",
    " ██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝",
    " ███████║██████╔╝██║     ███████║██║  ██║█████╗  ",
    " ██╔══██║██╔══██╗██║     ██╔══██║██║  ██║██╔══╝  ",
    " ██║  ██║██║  ██║╚██████╗██║  ██║██████╔╝███████╗",
    " ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═════╝ ╚══════╝",
]


@dataclass(frozen=True)
class ArcadeEntry:
    id: str
    title: str
    category: str
    subtitle: str
    blurb: str
    controls: str
    min_size: tuple[int, int]
    launch: Callable[[], None]


@dataclass(frozen=True)
class LauncherLayout:
    list_x: int
    list_y: int
    list_width: int
    list_height: int
    detail_x: int
    detail_y: int
    detail_width: int
    detail_height: int
    footer_y: int
    list_capacity: int

    @property
    def list_bottom(self) -> int:
        return self.list_y + self.list_height - 1

    @property
    def detail_bottom(self) -> int:
        return self.detail_y + self.detail_height - 1


def compute_layout(height: int, width: int, entry_count: int) -> LauncherLayout:
    """Compute a bounded launcher layout for the current terminal."""
    footer_y = height - 2
    panel_y = 10
    panel_height = max(8, min(18, footer_y - panel_y - 2))
    list_width = min(30, max(24, width // 3))
    list_x = 2
    detail_x = list_x + list_width + 2
    detail_width = max(20, width - detail_x - 2)
    raw_capacity = max(1, panel_height - 5)
    list_capacity = max(1, min(max(1, entry_count), raw_capacity))
    return LauncherLayout(
        list_x=list_x,
        list_y=panel_y,
        list_width=list_width,
        list_height=panel_height,
        detail_x=detail_x,
        detail_y=panel_y,
        detail_width=detail_width,
        detail_height=panel_height,
        footer_y=footer_y,
        list_capacity=list_capacity,
    )


def visible_window(selected: int, total: int, capacity: int) -> tuple[int, int]:
    """Return a viewport that always contains the selected entry."""
    if total <= 0:
        return 0, 0
    capacity = max(1, min(capacity, total))
    selected = max(0, min(selected, total - 1))
    start = max(0, min(selected - capacity + 1, total - capacity))
    return start, start + capacity


def init_colors() -> bool:
    """Initialize launcher colors when the terminal supports them."""
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


def build_entries() -> list[ArcadeEntry]:
    """Build the static launcher registry with lazy launch callables."""

    def launch_dino() -> None:
        from dino_game.game import run as run_dino

        run_dino(show_exit_message=False)

    def launch_snake() -> None:
        from snake_game.game import run as run_snake

        run_snake()

    def launch_bookshelf() -> None:
        from bookshelf.app import run as run_bookshelf

        run_bookshelf()

    def launch_chess() -> None:
        from chess_game.game import run as run_chess

        run_chess()

    def launch_tetris() -> None:
        from tetris_game.game import run as run_tetris

        run_tetris()

    def launch_star_blast() -> None:
        from star_blast.game import run as run_star_blast

        run_star_blast()

    def launch_kombat() -> None:
        from kombat_game.game import run as run_kombat

        run_kombat()

    def launch_wonder() -> None:
        from wonder.app import run as run_wonder

        run_wonder()

    def launch_polyglot() -> None:
        from polyglot.app import run as run_polyglot

        run_polyglot()

    return [
        ArcadeEntry(
            id="dino",
            title="Dino Run",
            category=GAME_CATEGORY,
            subtitle="Endless runner",
            blurb="Sprint through rotating biomes, pick your dinosaur, and use the roar meter to smash fragile hazards.",
            controls="SPACE or UP jump  |  DOWN duck  |  X roar  |  P pause  |  Q quit",
            min_size=(70, 20),
            launch=launch_dino,
        ),
        ArcadeEntry(
            id="snake",
            title="Snake",
            category=GAME_CATEGORY,
            subtitle="Classic Nokia snake",
            blurb="Chase food, avoid the walls, and manage the increasing speed as the snake grows across the grid.",
            controls="Arrows or WASD move  |  P pause  |  Q quit",
            min_size=(50, 20),
            launch=launch_snake,
        ),
        ArcadeEntry(
            id="tetris",
            title="Tetris",
            category=GAME_CATEGORY,
            subtitle="Classic endless stacker",
            blurb="Stack tetrominoes, chase line clears, and survive the accelerating pace with one next-piece preview.",
            controls="←/A left  |  →/D right  |  ↓/S drop  |  SPACE hard drop  |  X/↑ cw  |  Z ccw",
            min_size=(72, 26),
            launch=launch_tetris,
        ),
        ArcadeEntry(
            id="chess",
            title="Chess",
            category=GAME_CATEGORY,
            subtitle="Rule-based strategy duel",
            blurb="Play White against a built-in engine on a full-screen pixel board with denser piece sprites and legal-move hints.",
            controls="Arrows or hjkl move cursor  |  Space/Enter select  |  X cancel  |  undo/new/resign",
            min_size=(108, 48),
            launch=launch_chess,
        ),
        ArcadeEntry(
            id="star_blast",
            title="Star Blast",
            category=GAME_CATEGORY,
            subtitle="Large-sprite space shooter",
            blurb="Pilot a full-size terminal starship through asteroid fields, enemy craft, turret platforms, and carrier bosses.",
            controls="LEFT or A strafe  |  RIGHT or D strafe  |  HOLD SPACE fire  |  F autofire  |  Q quit",
            min_size=(96, 34),
            launch=launch_star_blast,
        ),
        ArcadeEntry(
            id="terminal_kombat",
            title="Terminal Kombat",
            category=GAME_CATEGORY,
            subtitle="Large-sprite 16-bit fighter",
            blurb="Pick an original warrior and fight huge terminal avatars with jumps, crouches, sweeps, throws, specials, finishers, and CPU pressure.",
            controls="A/D move  |  W jump  |  S crouch  |  J/K/U/O/H attacks  |  ; throw  |  L block  |  I special  |  F finisher",
            min_size=(118, 38),
            launch=launch_kombat,
        ),
        ArcadeEntry(
            id="bookshelf",
            title="Bookshelf",
            category=AMBIENT_CATEGORY,
            subtitle="Interactive quote explorer",
            blurb=f"Browse {BOOK_COUNT} curated books, open details, flip through quotes, and keep a lightweight personal collection.",
            controls="Arrows move  |  Enter open  |  / search  |  C collection  |  Q back or quit",
            min_size=(80, 24),
            launch=launch_bookshelf,
        ),
        ArcadeEntry(
            id="wonder",
            title="Wonder",
            category=AMBIENT_CATEGORY,
            subtitle="Daily fact or story",
            blurb="Pick a mood — funny, heartwarming, weird, or inspiring — and pull one fresh story or fact from the internet for the day. Saves your favorites for later.",
            controls="Arrows pick  |  Enter open  |  R refresh  |  S save  |  F favorites  |  Q back",
            min_size=(80, 24),
            launch=launch_wonder,
        ),
        ArcadeEntry(
            id="polyglot",
            title="Polyglot",
            category=AMBIENT_CATEGORY,
            subtitle="Learn a language",
            blurb=f"Pick one of {POLYGLOT_PAIR_COUNT} language pairs. Selecting a pair installs an ambient hook that surfaces alphabet, vocabulary, and sentences while you work.",
            controls="Arrows pick  |  Enter open  |  I install  |  C cadence  |  P print snippet  |  Q back",
            min_size=(96, 28),
            launch=launch_polyglot,
        ),
    ]


def move_selection(index: int, delta: int, total: int) -> int:
    """Move selection with wraparound."""
    if total <= 0:
        return 0
    return (index + delta) % total


def interpret_key(key: int, entry_count: int) -> tuple[str, int | None]:
    """Map a keypress to a launcher action."""
    if key in QUIT_KEYS:
        return "quit", None
    if key in MOVE_UP_KEYS:
        return "move", -1
    if key in MOVE_DOWN_KEYS:
        return "move", 1
    if key in LAUNCH_KEYS:
        return "launch", None
    if ord("1") <= key <= ord("9"):
        quick_index = key - ord("1")
        if quick_index < entry_count:
            return "launch_index", quick_index
    return "noop", None


def _draw_box(stdscr, y: int, x: int, width: int, height: int, attr: int = 0) -> None:
    if width < 2 or height < 2:
        return
    safe_addstr(stdscr, y, x, "╔" + "═" * (width - 2) + "╗", attr)
    for row in range(1, height - 1):
        safe_addstr(stdscr, y + row, x, "║", attr)
        safe_addstr(stdscr, y + row, x + width - 1, "║", attr)
    safe_addstr(stdscr, y + height - 1, x, "╚" + "═" * (width - 2) + "╝", attr)


def _render_small_terminal(stdscr, height: int, width: int) -> None:
    stdscr.erase()
    msg = f"Terminal too small ({width}x{height}). Need {MIN_WIDTH}x{MIN_HEIGHT}."
    hint = "Resize to browse the arcade. Press Q or Esc to quit."
    safe_addstr(stdscr, height // 2 - 1, max(0, (width - len(msg)) // 2), msg, curses.A_BOLD)
    safe_addstr(stdscr, height // 2 + 1, max(0, (width - len(hint)) // 2), hint, curses.A_DIM)
    stdscr.refresh()


def render(stdscr, entries: list[ArcadeEntry], selected: int, has_color: bool) -> None:
    """Render the launcher UI."""
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    if height < MIN_HEIGHT or width < MIN_WIDTH:
        _render_small_terminal(stdscr, height, width)
        return

    title_attr = curses.color_pair(2) | curses.A_BOLD if has_color else curses.A_BOLD
    sub_attr = curses.color_pair(5) | curses.A_BOLD if has_color else curses.A_BOLD
    box_attr = curses.color_pair(4) if has_color else curses.A_DIM
    accent_attr = curses.color_pair(1) | curses.A_BOLD if has_color else curses.A_BOLD
    meta_attr = curses.color_pair(3) | curses.A_BOLD if has_color else curses.A_BOLD
    selected_attr = (curses.color_pair(1) | curses.A_REVERSE | curses.A_BOLD) if has_color else (curses.A_REVERSE | curses.A_BOLD)

    y = 1
    for line in TITLE_ART:
        safe_addstr(stdscr, y, max(0, (width - len(line)) // 2), line, title_attr)
        y += 1

    subtitle = "Pick a cabinet, press play, and return here when you quit."
    safe_addstr(stdscr, y + 1, max(0, (width - len(subtitle)) // 2), subtitle, sub_attr)

    layout = compute_layout(height, width, len(entries))
    _draw_box(
        stdscr,
        layout.list_y,
        layout.list_x,
        layout.list_width,
        layout.list_height,
        box_attr,
    )
    _draw_box(
        stdscr,
        layout.detail_y,
        layout.detail_x,
        layout.detail_width,
        layout.detail_height,
        box_attr,
    )

    safe_addstr(stdscr, layout.list_y, layout.list_x + 2, " Cabinets ", accent_attr)
    safe_addstr(stdscr, layout.detail_y, layout.detail_x + 2, " Cabinet Card ", accent_attr)

    start, end = visible_window(selected, len(entries), layout.list_capacity)
    row_y = layout.list_y + 1
    last_category = None
    for idx in range(start, end):
        entry = entries[idx]
        if entry.category != last_category:
            category = CATEGORY_LABELS.get(entry.category, entry.category.title())
            safe_addstr(stdscr, row_y, layout.list_x + 2, f"── {category} ──", meta_attr)
            row_y += 1
            last_category = entry.category
        prefix = "▶" if idx == selected else " "
        label = f"{prefix} [{idx + 1}] {entry.title}"
        attr = selected_attr if idx == selected else curses.A_BOLD
        safe_addstr(stdscr, row_y, layout.list_x + 2, label, attr)
        row_y += 1

    scroll_parts = []
    if start > 0:
        scroll_parts.append("↑ more")
    if end < len(entries):
        scroll_parts.append("↓ more")
    if scroll_parts:
        safe_addstr(
            stdscr,
            layout.list_bottom - 1,
            layout.list_x + 2,
            "  ".join(scroll_parts),
            curses.A_DIM,
        )

    current = entries[selected]
    category = CATEGORY_LABELS.get(current.category, current.category.title())
    safe_addstr(stdscr, layout.detail_y + 2, layout.detail_x + 3, current.title, accent_attr)
    safe_addstr(
        stdscr,
        layout.detail_y + 2,
        layout.detail_x + layout.detail_width - 10,
        f"{selected + 1}/{len(entries)}",
        meta_attr,
    )
    safe_addstr(
        stdscr,
        layout.detail_y + 3,
        layout.detail_x + 3,
        f"{category} · {current.subtitle}",
        curses.A_DIM | curses.A_BOLD,
    )

    max_blurb_lines = max(1, layout.detail_height - 10)
    blurb_lines = textwrap.wrap(current.blurb, layout.detail_width - 6)[:max_blurb_lines]
    for offset, line in enumerate(blurb_lines):
        safe_addstr(stdscr, layout.detail_y + 5 + offset, layout.detail_x + 3, line)

    size_text = f"Needs terminal: {current.min_size[0]}x{current.min_size[1]}+"
    safe_addstr(
        stdscr,
        layout.detail_bottom - 4,
        layout.detail_x + 3,
        size_text,
        meta_attr,
    )

    controls_label = "Controls"
    safe_addstr(
        stdscr,
        layout.detail_bottom - 3,
        layout.detail_x + 3,
        controls_label,
        accent_attr,
    )
    for offset, line in enumerate(textwrap.wrap(current.controls, layout.detail_width - 6)[:2]):
        safe_addstr(
            stdscr,
            layout.detail_bottom - 2 + offset,
            layout.detail_x + 3,
            line,
            curses.A_DIM,
        )

    quick_launch = "1-9 quick launch" if len(entries) > 1 else "1 quick launch"
    footer = f"↑/↓ or j/k move   Enter/Space play   {quick_launch}   Q/Esc quit"
    safe_addstr(
        stdscr,
        layout.footer_y,
        max(0, (width - len(footer)) // 2),
        footer,
        curses.A_DIM,
    )
    stdscr.refresh()


def launcher_main(stdscr, entries: list[ArcadeEntry], initial_index: int = 0) -> int | None:
    """Run the curses launcher and return the selected entry index."""
    hide_cursor()
    stdscr.keypad(True)
    stdscr.timeout(100)
    has_color = init_colors()
    selected = max(0, min(initial_index, len(entries) - 1))

    while True:
        height, width = stdscr.getmaxyx()
        too_small = height < MIN_HEIGHT or width < MIN_WIDTH
        if too_small:
            _render_small_terminal(stdscr, height, width)
        else:
            render(stdscr, entries, selected, has_color)

        key = stdscr.getch()
        if key == -1:
            continue

        action, value = interpret_key(key, len(entries))
        if action == "quit":
            return None
        if too_small:
            continue
        if action == "move" and value is not None:
            selected = move_selection(selected, value, len(entries))
        elif action == "launch":
            return selected
        elif action == "launch_index" and value is not None:
            return value


def open_launcher(entries: list[ArcadeEntry], initial_index: int = 0) -> int | None:
    """Open the launcher in its own curses session."""
    try:
        return curses.wrapper(lambda stdscr: launcher_main(stdscr, entries, initial_index))
    except KeyboardInterrupt:
        return None


def run() -> None:
    """Entry point for the arcade launcher."""
    entries = build_entries()
    selected = 0

    while True:
        choice = open_launcher(entries, selected)
        if choice is None:
            return
        selected = choice
        entries[choice].launch()
