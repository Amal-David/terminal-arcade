import random
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from chess_game.core import (
    DIFFICULTIES,
    Position,
    apply_move,
    from_fen,
    game_outcome,
    generate_legal_moves,
    legal_move_from_text,
    parse_move,
    search_best_move,
)
from chess_game.storage import load_stats, save_stats


class ChessRulesTests(unittest.TestCase):
    def test_parse_move_supports_promotion_suffix(self) -> None:
        move = parse_move("e7e8q")
        self.assertIsNotNone(move)
        self.assertEqual("e7e8q", move.uci)

    def test_legal_move_from_text_accepts_basic_opening(self) -> None:
        position = Position()
        self.assertIsNotNone(legal_move_from_text(position, "e2e4"))
        self.assertIsNone(legal_move_from_text(position, "e2e5"))

    def test_castling_is_legal_when_lane_is_clear(self) -> None:
        position = from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
        legal = {move.uci for move in generate_legal_moves(position)}
        self.assertIn("e1g1", legal)
        self.assertIn("e1c1", legal)

    def test_en_passant_is_legal_when_available(self) -> None:
        position = from_fen("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1")
        self.assertIsNotNone(legal_move_from_text(position, "e5d6"))

    def test_promotion_moves_are_legal(self) -> None:
        position = from_fen("k7/4P3/8/8/8/8/8/4K3 w - - 0 1")
        self.assertIsNotNone(legal_move_from_text(position, "e7e8q"))
        self.assertIsNotNone(legal_move_from_text(position, "e7e8n"))

    def test_stalemate_is_reported(self) -> None:
        position = from_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
        self.assertEqual(("draw", "Stalemate"), game_outcome(position))

    def test_checkmate_is_reported(self) -> None:
        position = from_fen("7k/6Q1/6K1/8/8/8/8/8 b - - 0 1")
        self.assertEqual(("white", "Checkmate"), game_outcome(position))

    def test_fifty_move_rule_is_reported(self) -> None:
        position = from_fen("4k3/8/8/8/8/8/8/4K3 w - - 100 1")
        self.assertEqual(("draw", "Draw by fifty-move rule"), game_outcome(position))

    def test_repetition_is_reported(self) -> None:
        position = from_fen("4k2n/8/8/8/8/8/8/4K1N1 w - - 0 1")
        sequence = ["g1f3", "h8f7", "f3g1", "f7h8"] * 2
        for text in sequence:
            move = legal_move_from_text(position, text)
            self.assertIsNotNone(move)
            apply_move(position, move)
        self.assertEqual(("draw", "Draw by repetition"), game_outcome(position))


class ChessEngineTests(unittest.TestCase):
    def test_engine_finds_mate_in_one(self) -> None:
        position = from_fen("6k1/5ppp/8/8/8/6Q1/6PP/6K1 w - - 0 1")
        move = search_best_move(position, "hard", rng=random.Random(0))
        apply_move(position, move)
        self.assertEqual(("white", "Checkmate"), game_outcome(position))

    def test_engine_prefers_winning_capture(self) -> None:
        position = from_fen("4k3/8/8/3q4/4Q3/8/8/4K3 w - - 0 1")
        move = search_best_move(position, "medium", rng=random.Random(0))
        self.assertEqual("e4d5", move.uci)

    def test_difficulty_profiles_are_distinct(self) -> None:
        self.assertLess(DIFFICULTIES["easy"].max_depth, DIFFICULTIES["medium"].max_depth)
        self.assertLess(DIFFICULTIES["medium"].max_depth, DIFFICULTIES["hard"].max_depth)
        self.assertGreater(DIFFICULTIES["easy"].randomness, 0)
        self.assertEqual(0, DIFFICULTIES["hard"].randomness)


class ChessStorageTests(unittest.TestCase):
    def test_stats_round_trip(self) -> None:
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            stats = load_stats(base_dir)
            self.assertEqual("medium", stats["last_difficulty"])
            stats["wins"]["hard"] = 3
            stats["last_difficulty"] = "hard"
            save_stats(stats, base_dir)
            loaded = load_stats(base_dir)
            self.assertEqual(3, loaded["wins"]["hard"])
            self.assertEqual("hard", loaded["last_difficulty"])


if __name__ == "__main__":
    unittest.main()
