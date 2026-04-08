from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dino_game.storage import load_high_score, save_high_score, score_file_path


class StorageTests(unittest.TestCase):
    def test_high_score_round_trip(self) -> None:
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            self.assertEqual(load_high_score(base_dir), 0)
            save_high_score(245, base_dir)
            self.assertEqual(load_high_score(base_dir), 245)
            self.assertTrue(score_file_path(base_dir).exists())

    def test_invalid_score_file_falls_back_to_zero(self) -> None:
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            target = score_file_path(base_dir)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("{bad json", encoding="utf-8")
            self.assertEqual(load_high_score(base_dir), 0)
