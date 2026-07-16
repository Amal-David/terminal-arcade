"""Grid screen — pick one of N language pairs (paginated)."""

from __future__ import annotations

import curses

from polyglot.data.content_loader import ALL_PAIRS
from polyglot.data.pairs import LanguagePair
from polyglot.ui.widgets import draw_box, init_colors, safe_addstr
from terminal_arcade.ui import hide_cursor

GRID_COLS = 4
GRID_ROWS = 5
PAGE_SIZE = GRID_COLS * GRID_ROWS
CELL_WIDTH = 24
CELL_HEIGHT = 5

QUIT_KEYS = {ord("q"), ord("Q"), 27}
SELECT_KEYS = {curses.KEY_ENTER, 10, 13, ord(" ")}
INSTALL_KEYS = {ord("i"), ord("I")}
CADENCE_KEYS = {ord("c"), ord("C")}
NEXT_PAGE_KEYS = {curses.KEY_NPAGE, ord("n"), ord("N"), ord(">"), ord(".")}
PREV_PAGE_KEYS = {curses.KEY_PPAGE, ord("p"), ord("P"), ord("<"), ord(",")}


def _draw_cell(
    stdscr,
    y: int,
    x: int,
    pair: LanguagePair,
    selected: bool,
    active: bool,
    has_color: bool,
) -> None:
    box_attr = curses.color_pair(4) if has_color else 0
    if selected and has_color:
        box_attr = curses.color_pair(1) | curses.A_BOLD
    elif selected:
        box_attr = curses.A_BOLD
    draw_box(stdscr, y, x, CELL_WIDTH, CELL_HEIGHT, box_attr)

    flag = pair.flag if pair.flag else "  "
    label_attr = (
        curses.color_pair(2) | curses.A_BOLD if has_color else curses.A_BOLD
    ) if selected else (curses.color_pair(4) if has_color else 0)
    native_attr = curses.color_pair(5) | curses.A_DIM if has_color else curses.A_DIM
    status_attr = curses.color_pair(3) | curses.A_BOLD if has_color else curses.A_BOLD

    line1 = f"{flag}  {pair.source_lang} → {pair.target_lang}"
    safe_addstr(stdscr, y + 1, x + 2, line1[: CELL_WIDTH - 4], label_attr)
    safe_addstr(stdscr, y + 2, x + 2, pair.display_native[: CELL_WIDTH - 4], native_attr)
    badge = "● active" if active else ""
    if badge:
        safe_addstr(stdscr, y + 3, x + 2, badge, status_attr)


def _render(
    stdscr,
    selected: int,
    active_id: str | None,
    has_color: bool,
    status_line: str = "",
) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()

    total = len(ALL_PAIRS)
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    current_page = selected // PAGE_SIZE
    title = f"POLYGLOT — pick a language to learn   (page {current_page + 1}/{pages})"
    safe_addstr(
        stdscr,
        1,
        max(0, (width - len(title)) // 2),
        title,
        (curses.color_pair(2) | curses.A_BOLD) if has_color else curses.A_BOLD,
    )
    subtitle = (
        "Selecting a pair installs the ambient hook — every Nth tool call surfaces a phrase."
    )
    safe_addstr(
        stdscr,
        2,
        max(0, (width - len(subtitle)) // 2),
        subtitle,
        curses.A_DIM,
    )

    grid_w = GRID_COLS * (CELL_WIDTH + 1) - 1
    grid_h = GRID_ROWS * (CELL_HEIGHT + 1) - 1
    top = 4
    left = max(0, (width - grid_w) // 2)

    page_start = current_page * PAGE_SIZE
    page_end = min(page_start + PAGE_SIZE, total)
    for offset_idx, idx in enumerate(range(page_start, page_end)):
        if offset_idx >= PAGE_SIZE:
            break
        pair = ALL_PAIRS[idx]
        row = offset_idx // GRID_COLS
        col = offset_idx % GRID_COLS
        cy = top + row * (CELL_HEIGHT + 1)
        cx = left + col * (CELL_WIDTH + 1)
        if cy + CELL_HEIGHT > height - 2 or cx + CELL_WIDTH > width:
            continue
        _draw_cell(
            stdscr,
            cy,
            cx,
            pair,
            selected=(idx == selected),
            active=(pair.id == active_id),
            has_color=has_color,
        )

    bottom_y = top + grid_h + 1
    page_hint = f"Page {current_page + 1}/{pages} — {total} pairs total"
    safe_addstr(stdscr, bottom_y, max(0, (width - len(page_hint)) // 2), page_hint, curses.A_DIM)
    bottom_y += 1
    footer = "↑/↓/←/→ move   N/P next/prev page   Enter open   I install   C cadence   Q quit"
    if status_line:
        safe_addstr(stdscr, bottom_y, max(0, (width - len(status_line)) // 2), status_line, curses.A_BOLD)
        bottom_y += 1
    safe_addstr(stdscr, min(height - 2, bottom_y), max(0, (width - len(footer)) // 2), footer, curses.A_DIM)
    stdscr.refresh()


def _move(selected: int, dx: int, dy: int) -> int:
    total = len(ALL_PAIRS)
    if total == 0:
        return 0
    current_page = selected // PAGE_SIZE
    page_start = current_page * PAGE_SIZE
    page_end = min(page_start + PAGE_SIZE, total)
    rows_on_page = (page_end - page_start + GRID_COLS - 1) // GRID_COLS
    pos_in_page = selected - page_start
    row = pos_in_page // GRID_COLS
    col = pos_in_page % GRID_COLS
    new_col = (col + dx) % GRID_COLS
    new_row = (row + dy) % max(1, rows_on_page)
    new_pos = new_row * GRID_COLS + new_col
    new_idx = page_start + new_pos
    if new_idx >= page_end:
        new_idx = page_start + (new_pos % (page_end - page_start))
    return new_idx


def _jump_page(selected: int, delta: int) -> int:
    total = len(ALL_PAIRS)
    if total == 0:
        return 0
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    current_page = selected // PAGE_SIZE
    pos_in_page = selected - current_page * PAGE_SIZE
    new_page = (current_page + delta) % pages
    new_idx = new_page * PAGE_SIZE + pos_in_page
    if new_idx >= total:
        new_idx = min(total - 1, new_page * PAGE_SIZE)
    return new_idx


def open_grid(stdscr, *, initial: int = 0, status_line: str = "") -> tuple[str, int]:
    """Returns (action, idx) where action ∈ {'quit', 'open', 'install', 'cadence'}."""
    hide_cursor()
    stdscr.keypad(True)
    stdscr.timeout(150)
    has_color = init_colors()

    from polyglot.storage import get_active_pair_id

    selected = max(0, min(initial, len(ALL_PAIRS) - 1))
    active_id = get_active_pair_id()

    while True:
        _render(stdscr, selected, active_id, has_color, status_line)
        status_line = ""
        key = stdscr.getch()
        if key == -1:
            continue
        if key in QUIT_KEYS:
            return ("quit", selected)
        if key in SELECT_KEYS:
            return ("open", selected)
        if key in INSTALL_KEYS:
            return ("install", selected)
        if key in CADENCE_KEYS:
            return ("cadence", selected)
        if key in NEXT_PAGE_KEYS:
            selected = _jump_page(selected, 1)
        elif key in PREV_PAGE_KEYS:
            selected = _jump_page(selected, -1)
        elif key in (curses.KEY_LEFT, ord("h"), ord("H")):
            selected = _move(selected, -1, 0)
        elif key in (curses.KEY_RIGHT, ord("l"), ord("L")):
            selected = _move(selected, 1, 0)
        elif key in (curses.KEY_UP, ord("k"), ord("K")):
            selected = _move(selected, 0, -1)
        elif key in (curses.KEY_DOWN, ord("j"), ord("J")):
            selected = _move(selected, 0, 1)
        elif ord("1") <= key <= ord("9"):
            idx_in_page = key - ord("1")
            page_start = (selected // PAGE_SIZE) * PAGE_SIZE
            new_idx = page_start + idx_in_page
            if new_idx < len(ALL_PAIRS):
                selected = new_idx
