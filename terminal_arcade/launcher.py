"""Retro launcher for the terminal arcade collection."""

from __future__ import annotations

import curses
import textwrap
from dataclasses import dataclass
from typing import Callable

MIN_WIDTH = 80
MIN_HEIGHT = 24

MOVE_UP_KEYS = {curses.KEY_UP, ord("k"), ord("K")}
MOVE_DOWN_KEYS = {curses.KEY_DOWN, ord("j"), ord("J")}
LAUNCH_KEYS = {curses.KEY_ENTER, 10, 13, ord(" ")}
QUIT_KEYS = {ord("q"), ord("Q"), 27}
QUICK_LAUNCH_KEYS = {
    ord("1"): 0,
    ord("2"): 1,
    ord("3"): 2,
    ord("4"): 3,
}

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
    subtitle: str
    blurb: str
    controls: str
    min_size: tuple[int, int]
    launch: Callable[[], None]


def safe_addstr(stdscr, y: int, x: int, text: str, attr: int = 0) -> None:
    """Draw text while clipping to the visible terminal bounds."""
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

    def launch_star_blast() -> None:
        from star_blast.game import run as run_star_blast

        run_star_blast()

    return [
        ArcadeEntry(
            id="dino",
            title="Dino Run",
            subtitle="Endless runner",
            blurb="Sprint through rotating biomes, pick your dinosaur, and use the roar meter to smash fragile hazards.",
            controls="SPACE or UP jump  |  DOWN duck  |  X roar  |  P pause  |  Q quit",
            min_size=(70, 20),
            launch=launch_dino,
        ),
        ArcadeEntry(
            id="snake",
            title="Snake",
            subtitle="Classic Nokia snake",
            blurb="Chase food, avoid the walls, and manage the increasing speed as the snake grows across the grid.",
            controls="Arrows or WASD move  |  P pause  |  Q quit",
            min_size=(50, 20),
            launch=launch_snake,
        ),
        ArcadeEntry(
            id="star_blast",
            title="Star Blast",
            subtitle="Nokia-style space shooter",
            blurb="Pilot a larger starship through a tighter vertical arena and blast descending waves in campaign or endless mode.",
            controls="LEFT or A strafe  |  RIGHT or D strafe  |  HOLD SPACE fire  |  F autofire  |  Q quit",
            min_size=(72, 24),
            launch=launch_star_blast,
        ),
        ArcadeEntry(
            id="bookshelf",
            title="Bookshelf",
            subtitle="Interactive quote explorer",
            blurb="Browse curated books, open details, flip through quotes, and keep a lightweight personal collection.",
            controls="Arrows move  |  Enter open  |  / search  |  C collection  |  Q back or quit",
            min_size=(80, 24),
            launch=launch_bookshelf,
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
    if key in QUICK_LAUNCH_KEYS and QUICK_LAUNCH_KEYS[key] < entry_count:
        return "launch_index", QUICK_LAUNCH_KEYS[key]
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

    list_x = 4
    list_y = y + 4
    list_w = 28
    list_h = 11
    detail_x = list_x + list_w + 3
    detail_y = list_y
    detail_w = width - detail_x - 4
    detail_h = list_h + 4

    _draw_box(stdscr, list_y, list_x, list_w, list_h, box_attr)
    _draw_box(stdscr, detail_y, detail_x, detail_w, detail_h, box_attr)

    safe_addstr(stdscr, list_y, list_x + 2, " Cabinets ", accent_attr)
    safe_addstr(stdscr, detail_y, detail_x + 2, " Game Card ", accent_attr)

    for idx, entry in enumerate(entries):
        line_y = list_y + 2 + idx * 2
        prefix = "▶" if idx == selected else " "
        label = f"{prefix} [{idx + 1}] {entry.title}"
        attr = selected_attr if idx == selected else curses.A_BOLD
        safe_addstr(stdscr, line_y, list_x + 2, label, attr)
        safe_addstr(stdscr, line_y + 1, list_x + 6, entry.subtitle, curses.A_DIM)

    current = entries[selected]
    safe_addstr(stdscr, detail_y + 2, detail_x + 3, current.title, accent_attr)
    safe_addstr(stdscr, detail_y + 2, detail_x + detail_w - 10, f"{selected + 1}/{len(entries)}", meta_attr)

    for offset, line in enumerate(textwrap.wrap(current.blurb, detail_w - 6)):
        safe_addstr(stdscr, detail_y + 4 + offset, detail_x + 3, line)

    size_text = f"Needs terminal: {current.min_size[0]}x{current.min_size[1]}+"
    safe_addstr(stdscr, detail_y + detail_h - 5, detail_x + 3, size_text, meta_attr)

    controls_label = "Controls"
    safe_addstr(stdscr, detail_y + detail_h - 4, detail_x + 3, controls_label, accent_attr)
    for offset, line in enumerate(textwrap.wrap(current.controls, detail_w - 6)):
        safe_addstr(stdscr, detail_y + detail_h - 3 + offset, detail_x + 3, line, curses.A_DIM)

    footer = "↑/↓ or j/k move   Enter or Space play   1/2/3/4 quick launch   Q or Esc quit"
    safe_addstr(stdscr, height - 2, max(0, (width - len(footer)) // 2), footer, curses.A_DIM)
    stdscr.refresh()


def launcher_main(stdscr, entries: list[ArcadeEntry], initial_index: int = 0) -> int | None:
    """Run the curses launcher and return the selected entry index."""
    try:
        curses.curs_set(0)
    except curses.error:
        pass
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
