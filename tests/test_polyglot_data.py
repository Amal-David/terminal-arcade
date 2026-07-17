"""Polyglot data integrity tests — all 70 pair modules must shape up."""

from __future__ import annotations

import unittest

from polyglot.data.content_loader import ALL_PAIRS, get_pair, list_pairs
from polyglot.data.pairs import CATEGORIES, LanguagePair, PhraseEntry

EXPECTED_PAIR_COUNT = 70
MIN_PHRASES_PER_PAIR = 200


class PolyglotDataIntegrity(unittest.TestCase):
    def test_loads_exactly_seventy_pairs(self) -> None:
        self.assertEqual(EXPECTED_PAIR_COUNT, len(ALL_PAIRS))
        self.assertEqual(EXPECTED_PAIR_COUNT, len(list_pairs()))

    def test_pair_ids_are_unique(self) -> None:
        ids = [p.id for p in ALL_PAIRS]
        self.assertEqual(len(ids), len(set(ids)), f"duplicate pair ids: {ids}")

    def test_get_pair_round_trips(self) -> None:
        for p in ALL_PAIRS:
            self.assertIs(p, get_pair(p.id))
        self.assertIsNone(get_pair("does-not-exist"))

    def test_each_pair_meets_minimum_phrase_budget(self) -> None:
        for pair in ALL_PAIRS:
            with self.subTest(pair=pair.id):
                self.assertGreaterEqual(
                    len(pair.phrases),
                    MIN_PHRASES_PER_PAIR,
                    f"{pair.id} only has {len(pair.phrases)} phrases",
                )

    def test_phrase_entries_have_required_fields(self) -> None:
        for pair in ALL_PAIRS:
            for idx, entry in enumerate(pair.phrases):
                with self.subTest(pair=pair.id, idx=idx):
                    self.assertIsInstance(entry, PhraseEntry)
                    self.assertTrue(entry.source.strip(), f"empty source in {pair.id}[{idx}]")
                    self.assertTrue(entry.target.strip(), f"empty target in {pair.id}[{idx}]")
                    self.assertTrue(entry.pronunciation.strip(), f"empty pronunciation in {pair.id}[{idx}]")
                    self.assertIn(
                        entry.category,
                        CATEGORIES,
                        f"unknown category {entry.category!r} in {pair.id}[{idx}]",
                    )
                    self.assertTrue(entry.subcategory.strip(), f"empty subcategory in {pair.id}[{idx}]")

    def test_no_duplicate_targets_within_a_pair(self) -> None:
        for pair in ALL_PAIRS:
            targets = [e.target for e in pair.phrases]
            with self.subTest(pair=pair.id):
                self.assertEqual(
                    len(targets),
                    len(set(targets)),
                    f"duplicate targets within {pair.id}",
                )

    def test_pair_metadata_is_populated(self) -> None:
        for pair in ALL_PAIRS:
            with self.subTest(pair=pair.id):
                self.assertIsInstance(pair, LanguagePair)
                self.assertTrue(pair.id)
                self.assertTrue(pair.source_lang)
                self.assertTrue(pair.target_lang)
                self.assertTrue(pair.target_native)
                self.assertTrue(pair.script)
                self.assertTrue(pair.flag)
                self.assertTrue(pair.blurb)

    def test_each_pair_starts_with_a_script_entry_carrying_a_note(self) -> None:
        for pair in ALL_PAIRS:
            with self.subTest(pair=pair.id):
                first_script = next(
                    (e for e in pair.phrases if e.category == "script"), None
                )
                self.assertIsNotNone(first_script, f"no script entry in {pair.id}")
                self.assertTrue(
                    first_script.note.strip(),
                    f"first script entry of {pair.id} should carry a pronunciation note",
                )


if __name__ == "__main__":
    unittest.main()
