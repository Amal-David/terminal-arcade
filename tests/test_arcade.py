import curses
import unittest
from dataclasses import replace
from unittest.mock import patch

import dino_game.game as dino_game
import terminal_arcade.launcher as launcher
from terminal_arcade.launcher import (
    MIN_HEIGHT,
    MIN_WIDTH,
    build_entries,
    compute_layout,
    interpret_key,
    move_selection,
    open_launcher,
    visible_window,
)


class ArcadeLauncherTests(unittest.TestCase):
    def test_build_entries_has_expected_order_and_metadata(self) -> None:
        entries = build_entries()

        self.assertEqual(["dino", "snake", "tetris", "chess", "star_blast", "terminal_kombat", "bookshelf", "wonder", "polyglot"], [entry.id for entry in entries])
        self.assertEqual(["Dino Run", "Snake", "Tetris", "Chess", "Star Blast", "Terminal Kombat", "Bookshelf", "Wonder", "Polyglot"], [entry.title for entry in entries])
        self.assertEqual([(70, 20), (50, 20), (72, 26), (108, 48), (96, 34), (118, 38), (80, 24), (80, 24), (96, 28)], [entry.min_size for entry in entries])
        self.assertTrue(all(callable(entry.launch) for entry in entries))

    def test_move_selection_wraps_in_both_directions(self) -> None:
        self.assertEqual(2, move_selection(0, -1, 3))
        self.assertEqual(0, move_selection(2, 1, 3))

    def test_interpret_key_maps_navigation_launch_and_quit(self) -> None:
        self.assertEqual(("move", -1), interpret_key(curses.KEY_UP, 9))
        self.assertEqual(("move", 1), interpret_key(ord("j"), 9))
        self.assertEqual(("launch", None), interpret_key(10, 9))
        self.assertEqual(("launch_index", 2), interpret_key(ord("3"), 9))
        self.assertEqual(("launch_index", 5), interpret_key(ord("6"), 9))
        self.assertEqual(("launch_index", 7), interpret_key(ord("8"), 9))
        self.assertEqual(("launch_index", 8), interpret_key(ord("9"), 9))
        self.assertEqual(("quit", None), interpret_key(ord("q"), 5))

    def test_interpret_key_ignores_out_of_range_quick_launch(self) -> None:
        self.assertEqual(("noop", None), interpret_key(ord("7"), 6))
        self.assertEqual(("noop", None), interpret_key(ord("4"), 2))

    def test_open_launcher_returns_none_on_keyboard_interrupt(self) -> None:
        with patch("terminal_arcade.launcher.curses.wrapper", side_effect=KeyboardInterrupt):
            self.assertIsNone(open_launcher(build_entries()))

    def test_supported_minimum_keeps_panels_above_footer(self) -> None:
        layout = compute_layout(MIN_HEIGHT, MIN_WIDTH, len(build_entries()))

        self.assertLess(layout.list_bottom, layout.footer_y)
        self.assertLess(layout.detail_bottom, layout.footer_y)
        self.assertGreaterEqual(layout.list_capacity, 1)

    def test_visible_window_keeps_tenth_entry_in_a_bounded_viewport(self) -> None:
        entries = build_entries()
        entries.append(replace(entries[-1], id="extra", title="Extra Cabinet"))
        layout = compute_layout(MIN_HEIGHT, MIN_WIDTH, len(entries))

        start, end = visible_window(9, len(entries), layout.list_capacity)

        self.assertLessEqual(start, 9)
        self.assertGreater(end, 9)
        self.assertLessEqual(end - start, layout.list_capacity)

    def test_render_scrolls_to_a_tenth_entry(self) -> None:
        class MinimalScreen:
            def erase(self) -> None:
                pass

            def getmaxyx(self) -> tuple[int, int]:
                return MIN_HEIGHT, MIN_WIDTH

            def refresh(self) -> None:
                pass

        entries = build_entries()
        entries.append(replace(entries[-1], id="extra", title="Extra Cabinet"))
        drawn: list[str] = []

        with patch("terminal_arcade.launcher.curses.color_pair", return_value=0), patch(
            "terminal_arcade.launcher.safe_addstr",
            side_effect=lambda _screen, _y, _x, text, _attr=0: drawn.append(text),
        ):
            launcher.render(MinimalScreen(), entries, selected=9, has_color=False)

        self.assertTrue(any("Extra Cabinet" in text for text in drawn))
        self.assertTrue(any("↑ more" in text for text in drawn))

    def test_entries_expose_games_and_ambient_information_architecture(self) -> None:
        entries = build_entries()

        self.assertEqual(["game"] * 6 + ["ambient"] * 3, [entry.category for entry in entries])
        self.assertIn("983", entries[6].blurb)
        self.assertIn("70", entries[8].blurb)

    def test_render_stays_in_bounds_and_preserves_panel_bottoms(self) -> None:
        class RecordingScreen:
            def __init__(self) -> None:
                self.calls: list[tuple[int, int, str]] = []

            def erase(self) -> None:
                pass

            def getmaxyx(self) -> tuple[int, int]:
                return MIN_HEIGHT, MIN_WIDTH

            def addstr(self, y: int, x: int, text: str, _attr: int = 0) -> None:
                if not (0 <= y < MIN_HEIGHT and 0 <= x < MIN_WIDTH):
                    raise AssertionError(f"out-of-bounds draw at {x},{y}")
                self.calls.append((y, x, text))

            def refresh(self) -> None:
                pass

        screen = RecordingScreen()
        entries = build_entries()
        layout = compute_layout(MIN_HEIGHT, MIN_WIDTH, len(entries))

        with patch("terminal_arcade.launcher.curses.color_pair", return_value=0):
            launcher.render(screen, entries, selected=8, has_color=False)

        polyglot_rows = [
            y
            for y, x, text in screen.calls
            if "Polyglot" in text and x < layout.detail_x
        ]
        self.assertEqual(1, len(polyglot_rows))
        self.assertLess(polyglot_rows[0], layout.list_bottom)
        self.assertEqual(1, sum(y == layout.footer_y for y, _x, _text in screen.calls))
        self.assertEqual(2, sum(y == layout.list_bottom for y, _x, _text in screen.calls))
        self.assertEqual(2, sum(y == layout.detail_bottom for y, _x, _text in screen.calls))


class DinoRunTests(unittest.TestCase):
    def test_run_prints_exit_message_by_default(self) -> None:
        with patch("dino_game.game.curses.wrapper") as wrapper, patch("builtins.print") as print_mock:
            dino_game.run()

        wrapper.assert_called_once_with(dino_game.main)
        print_mock.assert_called_once_with("Thanks for playing Dino Run!")

    def test_run_can_suppress_exit_message(self) -> None:
        with patch("dino_game.game.curses.wrapper") as wrapper, patch("builtins.print") as print_mock:
            dino_game.run(show_exit_message=False)

        wrapper.assert_called_once_with(dino_game.main)
        print_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
