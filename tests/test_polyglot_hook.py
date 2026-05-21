"""Polyglot ambient hook tests — picker variety + cadence gating."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import polyglot.skill.config as polyglot_config
import polyglot.storage as polyglot_storage
from polyglot.skill.phrase_picker import (
    RECENT_WINDOW,
    pick_phrase,
    select_phrase_index,
    total_phrase_count,
)


def _with_isolated_state(test_method):
    """Decorator: route hook state + polyglot config to a tempdir."""

    def wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            state_file = tmp_path / "hook_state.json"

            real_load_config = polyglot_storage.load_config
            real_save_config = polyglot_storage.save_config

            def fake_load_config(base_dir=None):
                return real_load_config(tmp_path)

            def fake_save_config(cfg, base_dir=None):
                real_save_config(cfg, tmp_path)

            with patch.object(polyglot_config, "HOOK_STATE_FILE", state_file), \
                 patch.object(polyglot_storage, "load_config", fake_load_config), \
                 patch.object(polyglot_storage, "save_config", fake_save_config):
                test_method(self)

    return wrapper


class PhrasePickerVarietyTests(unittest.TestCase):
    def test_unseen_phrases_picked_before_repeats(self) -> None:
        phrases = list(range(5))  # length is what matters
        shown_counts = {"0": 2, "1": 1, "2": 0, "3": 0, "4": 0}
        recent = []
        idx = select_phrase_index(phrases, shown_counts, recent)
        self.assertIn(idx, {2, 3, 4})

    def test_recent_phrases_deprioritized(self) -> None:
        phrases = list(range(5))
        shown_counts: dict[str, int] = {}
        recent = [0, 1, 2]
        seen_outside_recent = 0
        for _ in range(40):
            idx = select_phrase_index(phrases, shown_counts, recent)
            if idx in (3, 4):
                seen_outside_recent += 1
        self.assertGreater(seen_outside_recent, 30)

    def test_recent_window_constant_is_finite(self) -> None:
        self.assertGreaterEqual(RECENT_WINDOW, 10)


class HookEndToEndTests(unittest.TestCase):
    @_with_isolated_state
    def test_pick_phrase_returns_none_without_active_pair(self) -> None:
        polyglot_storage.set_active_pair_id(None)
        self.assertIsNone(pick_phrase())

    @_with_isolated_state
    def test_pick_phrase_picks_from_active_pair(self) -> None:
        polyglot_storage.set_active_pair_id("en-es")
        result = pick_phrase()
        self.assertIsNotNone(result)
        self.assertEqual(result["pair_id"], "en-es")
        self.assertEqual(result["pair_label"], "English → Spanish")
        self.assertTrue(result["target"])
        self.assertEqual(result["unique_shown"], 1)

    @_with_isolated_state
    def test_pick_phrase_increments_shown_counts(self) -> None:
        polyglot_storage.set_active_pair_id("en-es")
        for _ in range(3):
            pick_phrase()
        state = polyglot_config.load_hook_state()
        self.assertEqual(state["total_phrases_shown"], 3)
        self.assertEqual(sum(state["shown_counts"].values()), 3)

    @_with_isolated_state
    def test_switching_pair_resets_history(self) -> None:
        polyglot_storage.set_active_pair_id("en-es")
        for _ in range(4):
            pick_phrase()
        state_a = polyglot_config.load_hook_state()
        self.assertEqual(state_a["total_phrases_shown"], 4)

        polyglot_storage.set_active_pair_id("en-ja")
        result = pick_phrase()
        self.assertEqual(result["pair_id"], "en-ja")
        state_b = polyglot_config.load_hook_state()
        # New pair → history is freshly reset and only the latest pick counts.
        self.assertEqual(state_b["total_phrases_shown"], 1)
        self.assertEqual(state_b["active_pair_id"], "en-ja")

    @_with_isolated_state
    def test_total_phrase_count_matches_pair_data(self) -> None:
        polyglot_storage.set_active_pair_id("en-es")
        from polyglot.data.content_loader import get_pair
        self.assertEqual(total_phrase_count(), len(get_pair("en-es").phrases))


class HookScriptTests(unittest.TestCase):
    """Smoke-test the actual hook.py entry point against an isolated state."""

    @_with_isolated_state
    def test_hook_returns_empty_when_no_active_pair(self) -> None:
        polyglot_storage.set_active_pair_id(None)
        import polyglot.skill.hook as hook
        with patch.object(sys, "stdin", _StubStdin('{"tool_name":"Bash"}')):
            with patch("builtins.print") as mock_print:
                hook.main()
        printed = mock_print.call_args[0][0]
        self.assertEqual(json.loads(printed), {})

    @_with_isolated_state
    def test_hook_returns_empty_off_cadence(self) -> None:
        polyglot_storage.set_active_pair_id("en-es")
        cfg = polyglot_storage.load_config()
        cfg["phrase_cadence"] = 5
        polyglot_storage.save_config(cfg)
        # First call: call_count=1, not divisible by 5 → empty.
        import polyglot.skill.hook as hook
        with patch.object(sys, "stdin", _StubStdin('{"tool_name":"Bash"}')):
            with patch("builtins.print") as mock_print:
                hook.main()
        printed = mock_print.call_args[0][0]
        self.assertEqual(json.loads(printed), {})

    @_with_isolated_state
    def test_hook_emits_system_message_on_cadence(self) -> None:
        polyglot_storage.set_active_pair_id("en-es")
        cfg = polyglot_storage.load_config()
        cfg["phrase_cadence"] = 1
        polyglot_storage.save_config(cfg)
        import polyglot.skill.hook as hook
        with patch.object(sys, "stdin", _StubStdin('{"tool_name":"Bash"}')):
            with patch("builtins.print") as mock_print:
                hook.main()
        printed = mock_print.call_args[0][0]
        payload = json.loads(printed)
        self.assertIn("systemMessage", payload)
        self.assertIn("English → Spanish", payload["systemMessage"])


class _StubStdin:
    """Minimal stand-in for sys.stdin so json.load can run on a fake stream."""

    def __init__(self, text: str) -> None:
        self._text = text

    def read(self) -> str:
        return self._text


if __name__ == "__main__":
    unittest.main()
