import json
import multiprocessing
import os
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from bookshelf.data.books import load_all_books
from dino_game.audio import AUDIO_DIR as DINO_AUDIO_DIR
from polyglot.data.content_loader import ALL_PAIRS
from star_blast.audio import AUDIO_DIR as STAR_BLAST_AUDIO_DIR
from terminal_arcade.catalog import BOOK_COUNT, POLYGLOT_PAIR_COUNT
from terminal_arcade.platform import app_data_dir, atomic_write_json, locked_json_update
from terminal_arcade.ui import hide_cursor


def _increment_locked_counter(path: str) -> None:
    def increment(state: dict) -> None:
        current = state.get("count", 0)
        time.sleep(0.002)
        state["count"] = current + 1

    locked_json_update(Path(path), {"count": 0}, increment)


class CatalogMetadataTests(unittest.TestCase):
    def test_declared_catalog_counts_match_runtime_registries(self) -> None:
        self.assertEqual(BOOK_COUNT, len(load_all_books()))
        self.assertEqual(POLYGLOT_PAIR_COUNT, len(ALL_PAIRS))


class RuntimeResourceTests(unittest.TestCase):
    def test_audio_resources_are_owned_by_their_packages(self) -> None:
        self.assertTrue(DINO_AUDIO_DIR.is_relative_to(Path(__file__).parents[1] / "dino_game"))
        self.assertTrue(STAR_BLAST_AUDIO_DIR.is_relative_to(Path(__file__).parents[1] / "star_blast"))
        self.assertTrue((DINO_AUDIO_DIR / "jump.wav").is_file())
        self.assertTrue((STAR_BLAST_AUDIO_DIR / "laser.wav").is_file())


class SharedPlatformTests(unittest.TestCase):
    def test_base_dir_override_preserves_existing_storage_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(Path(tmp), app_data_dir("demo", Path(tmp)))

    def test_atomic_json_write_replaces_temp_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "state.json"
            with patch("terminal_arcade.platform.os.replace", wraps=os.replace) as replace:
                atomic_write_json(target, {"score": 42})

            replace.assert_called_once()
            self.assertEqual({"score": 42}, json.loads(target.read_text(encoding="utf-8")))
            self.assertEqual([target], list(Path(tmp).iterdir()))

    def test_locked_json_update_serializes_concurrent_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "state.json"

            def increment() -> None:
                def update(state: dict) -> None:
                    current = state.get("count", 0)
                    time.sleep(0.001)
                    state["count"] = current + 1

                locked_json_update(target, {"count": 0}, update)

            with ThreadPoolExecutor(max_workers=12) as pool:
                list(pool.map(lambda _: increment(), range(50)))

            self.assertEqual(json.loads(target.read_text())["count"], 50)

    def test_locked_json_update_serializes_separate_processes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "state.json"
            context = multiprocessing.get_context("spawn")
            processes = [
                context.Process(target=_increment_locked_counter, args=(str(target),))
                for _ in range(12)
            ]
            for process in processes:
                process.start()
            for process in processes:
                process.join(timeout=10)
                self.assertEqual(process.exitcode, 0)

            self.assertEqual(json.loads(target.read_text())["count"], 12)

    def test_hide_cursor_tolerates_unsupported_terminal(self) -> None:
        with patch("terminal_arcade.ui.curses.curs_set", side_effect=OSError):
            hide_cursor()


if __name__ == "__main__":
    unittest.main()
