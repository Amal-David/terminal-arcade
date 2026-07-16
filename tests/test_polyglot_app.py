import unittest
from unittest.mock import patch

import polyglot.app as app


class PolyglotAppTests(unittest.TestCase):
    def test_invalid_cadence_confirmation_exits_cleanly_on_eof(self) -> None:
        with (
            patch("polyglot.skill.cadence.main"),
            patch("builtins.input", side_effect=["invalid", EOFError]),
            patch("builtins.print"),
        ):
            app._run_cadence_outside_curses()

    def test_keyboard_interrupt_during_out_of_curses_flow_exits_cleanly(self) -> None:
        with (
            patch("polyglot.app.curses.wrapper", return_value="cadence:any") as wrapper,
            patch("polyglot.app._run_cadence_outside_curses", side_effect=KeyboardInterrupt),
        ):
            app.run()

        wrapper.assert_called_once_with(app._curses_main)


if __name__ == "__main__":
    unittest.main()
