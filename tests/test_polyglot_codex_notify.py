"""Tests for the Codex notify hook — AppleScript escape and event filtering."""

from __future__ import annotations

import unittest

from polyglot.skill.codex_notify import _osascript_quote


class OsaScriptQuoteTests(unittest.TestCase):
    def test_double_quote_escaped(self) -> None:
        self.assertEqual(_osascript_quote('he said "hi"'), 'he said \\"hi\\"')

    def test_backslash_escaped_first(self) -> None:
        self.assertEqual(_osascript_quote("c:\\path"), "c:\\\\path")

    def test_newline_escaped_so_phrase_cant_break_out_of_string(self) -> None:
        self.assertEqual(_osascript_quote("line1\nline2"), "line1\\nline2")

    def test_carriage_return_escaped(self) -> None:
        self.assertEqual(_osascript_quote("a\rb"), "a\\rb")

    def test_tab_escaped(self) -> None:
        self.assertEqual(_osascript_quote("a\tb"), "a\\tb")

    def test_unicode_left_alone(self) -> None:
        # AppleScript handles UTF-8 strings fine; we should not mangle non-Latin glyphs.
        self.assertEqual(_osascript_quote("こんにちは"), "こんにちは")
        self.assertEqual(_osascript_quote("¿Qué pasa?"), "¿Qué pasa?")


if __name__ == "__main__":
    unittest.main()
