from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from bookshelf.storage import load_state, toggle_favorite


class BookshelfStorageIsolationTests(unittest.TestCase):
    def test_mutable_defaults_do_not_leak_between_data_directories(self) -> None:
        with TemporaryDirectory() as first, TemporaryDirectory() as second:
            toggle_favorite("The Left Hand of Darkness", Path(first))

            self.assertEqual(
                load_state(Path(first))["favorites"],
                ["The Left Hand of Darkness"],
            )
            self.assertEqual(load_state(Path(second))["favorites"], [])


if __name__ == "__main__":
    unittest.main()
