"""Pair detail — browse phrases by category."""

from __future__ import annotations

import curses
import textwrap

from polyglot.data.pairs import LanguagePair, PhraseEntry
from polyglot.ui.widgets import draw_box, init_colors, safe_addstr

CATEGORY_TABS = ("script", "vocab", "phrase", "sentence")
QUIT_KEYS = {ord("q"), ord("Q"), 27}
INSTALL_KEYS = {ord("i"), ord("I")}
PRINT_KEYS = {ord("p"), ord("P")}
CADENCE_KEYS = {ord("c"), ord("C")}
NEXT_TAB_KEYS = {ord("\t"), curses.KEY_RIGHT, ord("l"), ord("L")}
PREV_TAB_KEYS = {curses.KEY_LEFT, ord("h"), ord("H"), curses.KEY_BTAB}
SCROLL_UP_KEYS = {curses.KEY_UP, ord("k"), ord("K")}
SCROLL_DOWN_KEYS = {curses.KEY_DOWN, ord("j"), ord("J")}
PAGE_UP_KEYS = {curses.KEY_PPAGE, ord("u"), ord("U")}
PAGE_DOWN_KEYS = {curses.KEY_NPAGE, ord("d"), ord("D")}


def _phrases_for_tab(pair: LanguagePair, tab: str) -> list[PhraseEntry]:
    return [p for p in pair.phrases if p.category == tab]


def _render(
    stdscr,
    pair: LanguagePair,
    tab_idx: int,
    scroll: int,
    has_color: bool,
    active: bool,
) -> int:
    stdscr.erase()
    height, width = stdscr.getmaxyx()

    title = f"{pair.flag}  {pair.source_lang} → {pair.target_lang}  ({pair.display_native})"
    title_attr = curses.color_pair(2) | curses.A_BOLD if has_color else curses.A_BOLD
    safe_addstr(stdscr, 1, max(0, (width - len(title)) // 2), title, title_attr)

    sub_parts = [f"script: {pair.script}", f"{len(pair.phrases)} phrases"]
    if active:
        sub_parts.append("● ACTIVE")
    sub_attr = curses.color_pair(3) | curses.A_DIM if has_color else curses.A_DIM
    sub = "  |  ".join(sub_parts)
    safe_addstr(stdscr, 2, max(0, (width - len(sub)) // 2), sub, sub_attr)

    blurb_lines = textwrap.wrap(pair.blurb, max(20, width - 8))
    for offset, line in enumerate(blurb_lines[:2]):
        safe_addstr(stdscr, 3 + offset, max(0, (width - len(line)) // 2), line, curses.A_DIM)

    tab_y = 6
    tab_labels = []
    for i, name in enumerate(CATEGORY_TABS):
        count = sum(1 for p in pair.phrases if p.category == name)
        tab_labels.append(f"{name.capitalize()} ({count})")
    total_width = sum(len(t) + 4 for t in tab_labels)
    tab_x = max(2, (width - total_width) // 2)
    for i, label in enumerate(tab_labels):
        attr = (
            curses.color_pair(1) | curses.A_REVERSE | curses.A_BOLD
            if i == tab_idx and has_color
            else (curses.A_REVERSE | curses.A_BOLD if i == tab_idx else curses.A_DIM)
        )
        safe_addstr(stdscr, tab_y, tab_x, f" {label} ", attr)
        tab_x += len(label) + 4

    box_top = tab_y + 2
    box_h = max(8, height - box_top - 4)
    box_attr = curses.color_pair(4) if has_color else 0
    draw_box(stdscr, box_top, 2, width - 4, box_h, box_attr)

    phrases = _phrases_for_tab(pair, CATEGORY_TABS[tab_idx])
    inner_h = box_h - 2
    if scroll < 0:
        scroll = 0
    max_scroll = max(0, len(phrases) - inner_h)
    if scroll > max_scroll:
        scroll = max_scroll

    for row in range(inner_h):
        idx = scroll + row
        if idx >= len(phrases):
            break
        entry = phrases[idx]
        target_attr = curses.color_pair(2) | curses.A_BOLD if has_color else curses.A_BOLD
        pron_attr = curses.color_pair(5) | curses.A_DIM if has_color else curses.A_DIM
        source_attr = curses.A_NORMAL

        target = entry.target
        source = f"  — {entry.source}"
        pron = f"  [{entry.pronunciation}]" if entry.pronunciation else ""
        sub = f"  · {entry.subcategory}"

        y = box_top + 1 + row
        x = 4
        safe_addstr(stdscr, y, x, target, target_attr)
        cursor = x + min(20, len(target))
        safe_addstr(stdscr, y, cursor, source, source_attr)
        cursor += len(source)
        safe_addstr(stdscr, y, cursor, pron, pron_attr)
        cursor += len(pron)
        safe_addstr(stdscr, y, cursor, sub, curses.A_DIM)

    if len(phrases) > inner_h:
        scroll_info = f"  {scroll + 1}-{min(scroll + inner_h, len(phrases))}/{len(phrases)}  "
        safe_addstr(stdscr, box_top, width - len(scroll_info) - 4, scroll_info, curses.A_DIM)

    footer = "Tab/←/→ tabs   ↑/↓ scroll   I install   C cadence   P print snippet   Q back"
    safe_addstr(stdscr, height - 2, max(0, (width - len(footer)) // 2), footer, curses.A_DIM)
    stdscr.refresh()
    return scroll


def open_detail(stdscr, pair: LanguagePair) -> str:
    """Returns one of 'back', 'install', 'cadence', 'print'."""
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.keypad(True)
    stdscr.timeout(150)
    has_color = init_colors()

    from polyglot.storage import get_active_pair_id

    tab_idx = 0
    scroll = 0
    while True:
        active = get_active_pair_id() == pair.id
        scroll = _render(stdscr, pair, tab_idx, scroll, has_color, active)
        key = stdscr.getch()
        if key == -1:
            continue
        if key in QUIT_KEYS:
            return "back"
        if key in INSTALL_KEYS:
            return "install"
        if key in CADENCE_KEYS:
            return "cadence"
        if key in PRINT_KEYS:
            return "print"
        if key in NEXT_TAB_KEYS:
            tab_idx = (tab_idx + 1) % len(CATEGORY_TABS)
            scroll = 0
        elif key in PREV_TAB_KEYS:
            tab_idx = (tab_idx - 1) % len(CATEGORY_TABS)
            scroll = 0
        elif key in SCROLL_UP_KEYS:
            scroll -= 1
        elif key in SCROLL_DOWN_KEYS:
            scroll += 1
        elif key in PAGE_UP_KEYS:
            scroll -= 8
        elif key in PAGE_DOWN_KEYS:
            scroll += 8
