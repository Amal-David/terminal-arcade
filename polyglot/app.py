"""Polyglot cabinet — curses launcher for browsing 20 language pairs."""

from __future__ import annotations

import curses
import sys

from polyglot.data.content_loader import ALL_PAIRS
from polyglot.screens.grid import open_grid
from polyglot.screens.installer_screen import run_install_flow
from polyglot.screens.pair_detail import open_detail


def _run_cadence_outside_curses() -> None:
    from polyglot.skill.cadence import main as cadence_main
    print()
    print("Current cadence:")
    cadence_main([])
    print()
    try:
        raw = input("New cadence value (blank to keep, append ' c' for codex-only or ' b' for both): ").strip()
    except EOFError:
        raw = ""
    if not raw:
        return
    parts = raw.split()
    try:
        value = int(parts[0])
    except ValueError:
        print(f"Invalid cadence: {parts[0]}")
        input("Press Enter to continue...")
        return
    suffix = parts[1].lower() if len(parts) > 1 else ""
    args = [str(value)]
    if suffix.startswith("c"):
        args.append("--codex")
    elif suffix.startswith("b"):
        args.append("--both")
    cadence_main(args)
    print()
    try:
        input("Press Enter to return to the cabinet...")
    except EOFError:
        pass


def _curses_main(stdscr) -> str | None:
    initial = 0
    status_line = ""
    while True:
        action, idx = open_grid(stdscr, initial=initial, status_line=status_line)
        status_line = ""
        if action == "quit":
            return None
        pair = ALL_PAIRS[idx]
        initial = idx
        if action == "install":
            return f"install:{pair.id}"
        if action == "cadence":
            return f"cadence:{pair.id}"
        if action == "open":
            sub_action = open_detail(stdscr, pair)
            if sub_action == "install":
                return f"install:{pair.id}"
            if sub_action == "cadence":
                return f"cadence:{pair.id}"
            if sub_action == "print":
                return f"print:{pair.id}"


def run() -> None:
    """Entry point — wrap curses, dispatch out-of-curses install/cadence flows."""
    while True:
        try:
            command = curses.wrapper(_curses_main)
        except KeyboardInterrupt:
            return
        if not command:
            return

        verb, _, pair_id = command.partition(":")
        pair = next((p for p in ALL_PAIRS if p.id == pair_id), None)

        if verb == "install" and pair:
            run_install_flow(pair, print_only=False)
        elif verb == "print" and pair:
            run_install_flow(pair, print_only=True)
        elif verb == "cadence":
            _run_cadence_outside_curses()


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        sys.exit(0)
