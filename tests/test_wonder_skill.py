"""Tests for the wonder.skill hook, cadence CLI, and picker."""

from __future__ import annotations

import datetime as _dt
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from wonder.skill import cadence, codex_notify, hook  # noqa: E402
from wonder.skill import config as skill_config  # noqa: E402
from wonder.skill import wonder_picker  # noqa: E402


class WonderPickerTest(unittest.TestCase):
    def test_today_category_rotates_deterministically(self) -> None:
        with mock.patch.object(wonder_picker, "get_category_preference", return_value="rotate"):
            cat = wonder_picker.today_category()
        self.assertIn(cat, {"funny", "heartwarming", "weird", "inspiring"})

    def test_today_category_honors_pinned_choice(self) -> None:
        with mock.patch.object(wonder_picker, "get_category_preference", return_value="funny"):
            self.assertEqual(wonder_picker.today_category(), "funny")

    def test_pick_wonder_from_cache_when_available(self) -> None:
        today = _dt.date.today().isoformat()
        story = {
            "category": "weird",
            "title": "Did you know?",
            "body": "Octopuses have three hearts.",
            "source": "uselessfacts.jsph.pl",
            "url": None,
            "fetched_at": today,
            "origin": "live",
        }
        cache = {today: {"weird": story}}
        with mock.patch.object(wonder_picker, "load_cache", return_value=cache):
            picked = wonder_picker.pick_wonder("weird")
        self.assertEqual(picked["origin"], "cache")
        self.assertEqual(picked["body"], story["body"])

    def test_pick_wonder_falls_back_to_bundle(self) -> None:
        with mock.patch.object(wonder_picker, "load_cache", return_value={}):
            picked = wonder_picker.pick_wonder("funny")
        self.assertEqual(picked["origin"], "fallback")
        self.assertTrue(picked["body"])

    def test_format_system_message_includes_category_and_body(self) -> None:
        story = {
            "category": "weird",
            "title": "Did you know?",
            "body": "Honey never spoils.",
            "source": "uselessfacts.jsph.pl",
            "origin": "cache",
        }
        msg = wonder_picker.format_system_message(story)
        self.assertIn("Weird Facts", msg)
        self.assertIn("Honey never spoils.", msg)
        self.assertIn("uselessfacts.jsph.pl", msg)

    def test_format_notification_truncates_long_body(self) -> None:
        story = {
            "category": "inspiring",
            "title": "Long",
            "body": "x" * 500,
            "source": "Bundled",
            "origin": "fallback",
        }
        title, body = wonder_picker.format_notification(story)
        self.assertIn("Inspiring", title)
        self.assertLessEqual(len(body), wonder_picker.NOTIFY_BODY_MAX)


class ShouldFireTest(unittest.TestCase):
    def test_daily_fires_once_per_day(self) -> None:
        state: dict = {}
        self.assertTrue(hook._should_fire("daily", state))
        self.assertFalse(hook._should_fire("daily", state))

    def test_off_never_fires(self) -> None:
        state: dict = {}
        self.assertFalse(hook._should_fire("off", state))
        self.assertEqual(state, {})

    def test_n_mode_fires_every_n(self) -> None:
        state: dict = {}
        outcomes = [hook._should_fire(3, state) for _ in range(7)]
        self.assertEqual(outcomes, [False, False, True, False, False, True, False])

    def test_codex_daily_fires_once_per_day(self) -> None:
        state: dict = {}
        self.assertTrue(codex_notify._should_fire("daily", state))
        self.assertFalse(codex_notify._should_fire("daily", state))

    def test_codex_n_mode_fires_every_n(self) -> None:
        state: dict = {}
        outcomes = [codex_notify._should_fire(2, state) for _ in range(5)]
        self.assertEqual(outcomes, [False, True, False, True, False])


class CadenceCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self._config: dict = {}

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

    def test_show_defaults(self) -> None:
        out = self._run([])
        self.assertIn("once per day", out)
        self.assertIn("rotate", out)

    def test_set_daily_claude(self) -> None:
        self._run(["daily"])
        self.assertEqual(self._config["wonder_cadence"], "daily")
        self.assertNotIn("codex_wonder_cadence", self._config)

    def test_set_integer_codex(self) -> None:
        self._run(["7", "--codex"])
        self.assertEqual(self._config["codex_wonder_cadence"], 7)
        self.assertNotIn("wonder_cadence", self._config)

    def test_set_off_both(self) -> None:
        self._run(["off", "--both"])
        self.assertEqual(self._config["wonder_cadence"], "off")
        self.assertEqual(self._config["codex_wonder_cadence"], "off")

    def test_set_category_funny(self) -> None:
        self._run(["--category", "funny"])
        self.assertEqual(self._config["wonder_category"], "funny")

    def test_rejects_zero(self) -> None:
        with self.assertRaises(SystemExit):
            cadence.main(["0"])

    def test_rejects_garbage(self) -> None:
        with self.assertRaises(SystemExit):
            cadence.main(["nope"])

    def test_rejects_invalid_category(self) -> None:
        with self.assertRaises(SystemExit):
            cadence.main(["--category", "nonexistent"])


class ConfigNormalizationTest(unittest.TestCase):
    def test_daily_string_passes_through(self) -> None:
        self.assertEqual(skill_config._normalize_cadence("daily", "daily"), "daily")

    def test_off_string_passes_through(self) -> None:
        self.assertEqual(skill_config._normalize_cadence("off", "daily"), "off")

    def test_integer_string_parses(self) -> None:
        self.assertEqual(skill_config._normalize_cadence("5", "daily"), 5)

    def test_zero_falls_back_to_default(self) -> None:
        self.assertEqual(skill_config._normalize_cadence("0", "daily"), "daily")

    def test_garbage_falls_back_to_default(self) -> None:
        self.assertEqual(skill_config._normalize_cadence("garbage", "daily"), "daily")


if __name__ == "__main__":
    unittest.main()
