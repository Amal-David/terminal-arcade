import curses
import unittest
from unittest.mock import patch

import dino_game.game as dino_game
from terminal_arcade.launcher import build_entries, interpret_key, move_selection, open_launcher


class ArcadeLauncherTests(unittest.TestCase):
    def test_build_entries_has_expected_order_and_metadata(self) -> None:
        entries = build_entries()

        self.assertEqual(["dino", "snake", "star_blast", "bookshelf"], [entry.id for entry in entries])
        self.assertEqual(["Dino Run", "Snake", "Star Blast", "Bookshelf"], [entry.title for entry in entries])
        self.assertEqual([(70, 20), (50, 20), (72, 24), (80, 24)], [entry.min_size for entry in entries])
        self.assertTrue(all(callable(entry.launch) for entry in entries))

    def test_move_selection_wraps_in_both_directions(self) -> None:
        self.assertEqual(2, move_selection(0, -1, 3))
        self.assertEqual(0, move_selection(2, 1, 3))

    def test_interpret_key_maps_navigation_launch_and_quit(self) -> None:
        self.assertEqual(("move", -1), interpret_key(curses.KEY_UP, 4))
        self.assertEqual(("move", 1), interpret_key(ord("j"), 4))
        self.assertEqual(("launch", None), interpret_key(10, 4))
        self.assertEqual(("launch_index", 1), interpret_key(ord("2"), 4))
        self.assertEqual(("launch_index", 3), interpret_key(ord("4"), 4))
        self.assertEqual(("quit", None), interpret_key(ord("q"), 4))

    def test_interpret_key_ignores_out_of_range_quick_launch(self) -> None:
        self.assertEqual(("noop", None), interpret_key(ord("4"), 2))

    def test_open_launcher_returns_none_on_keyboard_interrupt(self) -> None:
        with patch("terminal_arcade.launcher.curses.wrapper", side_effect=KeyboardInterrupt):
            self.assertIsNone(open_launcher(build_entries()))


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
