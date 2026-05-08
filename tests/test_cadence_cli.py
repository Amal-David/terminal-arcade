"""Tests for the bookshelf.skill.cadence CLI."""

from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bookshelf.skill import cadence  # noqa: E402


class CadenceCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self._config: dict = {"quote_cadence": 5, "codex_quote_cadence": 5}

        def fake_load() -> dict:
            return dict(self._config)

        def fake_save(config: dict) -> None:
            self._config = dict(config)

        self._load_patch = mock.patch.object(cadence, "load_config", side_effect=fake_load)
        self._save_patch = mock.patch.object(cadence, "save_config", side_effect=fake_save)
        self._load_patch.start()
        self._save_patch.start()

    def tearDown(self) -> None:
        self._load_patch.stop()
        self._save_patch.stop()

    def _run(self, argv: list[str]) -> str:
        buf = io.StringIO()
        with mock.patch("sys.stdout", buf):
            rc = cadence.main(argv)
        self.assertEqual(rc, 0)
        return buf.getvalue()

    def test_show_default(self) -> None:
        out = self._run([])
        self.assertIn("every 5 tool calls", out)
        self.assertIn("every 5 turns", out)

    def test_set_claude_only(self) -> None:
        self._run(["10"])
        self.assertEqual(self._config["quote_cadence"], 10)
        self.assertEqual(self._config["codex_quote_cadence"], 5)

    def test_set_codex_only(self) -> None:
        self._run(["20", "--codex"])
        self.assertEqual(self._config["quote_cadence"], 5)
        self.assertEqual(self._config["codex_quote_cadence"], 20)

    def test_set_both(self) -> None:
        self._run(["10", "--both"])
        self.assertEqual(self._config["quote_cadence"], 10)
        self.assertEqual(self._config["codex_quote_cadence"], 10)

    def test_rejects_zero(self) -> None:
        with self.assertRaises(SystemExit):
            cadence.main(["0"])

    def test_rejects_negative(self) -> None:
        with self.assertRaises(SystemExit):
            cadence.main(["-3"])


if __name__ == "__main__":
    unittest.main()
