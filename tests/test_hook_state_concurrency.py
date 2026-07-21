import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bookshelf.skill.codex_notify as bookshelf_notify
import bookshelf.skill.config as bookshelf_config
from bookshelf.skill.quote_picker import pick_quote
import polyglot.skill.codex_notify as polyglot_notify
import polyglot.skill.config as polyglot_config
from polyglot.skill.phrase_picker import pick_phrase
import wonder.skill.codex_notify as wonder_notify
import wonder.skill.config as wonder_config


def _run_concurrently(callback, count: int = 40) -> None:
    with ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(lambda _: callback(), range(count)))


class HookStateConcurrencyTests(unittest.TestCase):
    def test_polyglot_codex_turn_counter_does_not_lose_updates(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "hook_state.json"
            with patch.object(polyglot_config, "HOOK_STATE_FILE", state_path), patch.object(
                polyglot_config, "get_active_pair_id", return_value="en-es"
            ), patch.object(polyglot_config, "get_codex_cadence", return_value=10_000):
                _run_concurrently(
                    lambda: polyglot_notify.main(["codex_notify.py", "turn-ended", "{}"])
                )

            self.assertEqual(json.loads(state_path.read_text())["codex_turn_count"], 40)

    def test_bookshelf_codex_turn_counter_does_not_lose_updates(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "hook_state.json"
            with patch.object(bookshelf_config, "HOOK_STATE_FILE", state_path), patch.object(
                bookshelf_config, "get_codex_cadence", return_value=10_000
            ):
                _run_concurrently(
                    lambda: bookshelf_notify.main(["codex_notify.py", "turn-ended", "{}"])
                )

            self.assertEqual(json.loads(state_path.read_text())["codex_turn_count"], 40)

    def test_wonder_codex_turn_counter_does_not_lose_updates(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "hook_state.json"
            with patch.object(wonder_config, "_state_path", return_value=state_path), patch.object(
                wonder_config, "get_codex_cadence", return_value=10_000
            ):
                _run_concurrently(
                    lambda: wonder_notify.main(["codex_notify.py", "turn-ended", "{}"])
                )

            self.assertEqual(json.loads(state_path.read_text())["codex_turn_count"], 40)

    def test_polyglot_phrase_history_does_not_lose_concurrent_picks(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "hook_state.json"
            with patch.object(polyglot_config, "HOOK_STATE_FILE", state_path):
                _run_concurrently(lambda: pick_phrase("en-es"), count=25)

            state = json.loads(state_path.read_text())
            self.assertEqual(state["total_phrases_shown"], 25)
            self.assertEqual(sum(state["shown_counts"].values()), 25)

    def test_bookshelf_quote_history_does_not_lose_concurrent_picks(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "hook_state.json"
            with patch.object(bookshelf_config, "HOOK_STATE_FILE", state_path):
                _run_concurrently(pick_quote, count=25)

            state = json.loads(state_path.read_text())
            self.assertEqual(state["total_quotes_shown"], 25)
            self.assertEqual(sum(state["shown_counts"].values()), 25)


if __name__ == "__main__":
    unittest.main()
