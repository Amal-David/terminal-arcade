import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bookshelf.skill.config as cfg
import bookshelf.skill.codex_notify as codex_notify


class CodexNotifyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self._state_file = Path(self._tmpdir.name) / "hook_state.json"

        # Redirect bookshelf state to a tmp file so tests don't touch real state.
        self._state_patch = patch.object(cfg, "HOOK_STATE_FILE", self._state_file)
        self._state_patch.start()
        self.addCleanup(self._state_patch.stop)

        # Force a deterministic cadence regardless of user config.
        self._cadence_patch = patch.object(cfg, "get_codex_cadence", return_value=5)
        self._cadence_patch.start()
        self.addCleanup(self._cadence_patch.stop)

    def _read_state(self) -> dict:
        if not self._state_file.exists():
            return {}
        return json.loads(self._state_file.read_text(encoding="utf-8"))

    def test_turn_ended_fires_quote_every_fifth_turn_on_macos(self) -> None:
        with patch.object(codex_notify.sys, "platform", "darwin"), patch.object(
            codex_notify.subprocess, "run"
        ) as run_mock:
            for _ in range(10):
                codex_notify.main(["codex_notify.py", "turn-ended", "{}"])

        self.assertEqual(run_mock.call_count, 2)
        for call in run_mock.call_args_list:
            cmd = call.args[0]
            self.assertEqual(cmd[0], "osascript")
            self.assertIn("display notification", cmd[2])

        self.assertEqual(self._read_state().get("codex_turn_count"), 10)

    def test_non_turn_ended_events_are_noops(self) -> None:
        with patch.object(codex_notify.subprocess, "run") as run_mock:
            for event in ("turn-started", "session-started", "tool-called", ""):
                codex_notify.main(["codex_notify.py", event, "{}"])

        run_mock.assert_not_called()
        self.assertEqual(self._read_state().get("codex_turn_count", 0), 0)

    def test_state_persists_between_invocations(self) -> None:
        with patch.object(codex_notify.subprocess, "run"):
            codex_notify.main(["codex_notify.py", "turn-ended", "{}"])
            codex_notify.main(["codex_notify.py", "turn-ended", "{}"])

        self.assertEqual(self._read_state().get("codex_turn_count"), 2)

        with patch.object(codex_notify.subprocess, "run"):
            codex_notify.main(["codex_notify.py", "turn-ended", "{}"])

        self.assertEqual(self._read_state().get("codex_turn_count"), 3)

    def test_non_macos_falls_back_to_stderr(self) -> None:
        captured = []

        def fake_write(text: str) -> int:
            captured.append(text)
            return len(text)

        with patch.object(codex_notify.sys, "platform", "linux"), patch.object(
            codex_notify.sys.stderr, "write", side_effect=fake_write
        ), patch.object(codex_notify.subprocess, "run") as run_mock:
            for _ in range(5):
                codex_notify.main(["codex_notify.py", "turn-ended", "{}"])

        run_mock.assert_not_called()
        self.assertTrue(any("📖" in chunk for chunk in captured))


if __name__ == "__main__":
    unittest.main()
