import random
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest

from chess_game.core import (
    DIFFICULTIES,
    Position,
    SearchContext,
    SearchTimeout,
    apply_move,
    from_fen,
    game_outcome,
    generate_legal_moves,
    legal_move_from_text,
    negamax,
    position_key,
    parse_move,
    search_best_move,
)
from chess_game.game import (
    ENGINE_THINK_DELAY,
    GameState,
    append_log,
    build_selected_move_text,
    clear_selection,
    drive_engine_turn,
    legal_destinations_for_selection,
    move_cursor,
    piece_sprite,
    process_command,
    select_or_play_cursor_square,
    start_new_game,
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

    def test_search_timeout_restores_position(self) -> None:
        position = Position()
        before_key = position_key(position)
        context = SearchContext(
            difficulty=DIFFICULTIES["hard"],
            deadline=time.perf_counter() + 10,
            node_limit=2,
        )

        with self.assertRaises(SearchTimeout):
            negamax(position, 3, -100_000, 100_000, context)

        self.assertEqual(before_key, position_key(position))
        self.assertTrue(position.white_to_move)


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


class ChessControlTests(unittest.TestCase):
    def test_piece_sprite_draws_multi_line_pixel_piece(self) -> None:
        sprite = piece_sprite("Q")
        self.assertEqual(5, len(sprite))
        self.assertTrue(all(len(line) == 10 for line in sprite))
        self.assertTrue(any("█" in line for line in sprite))

    def test_move_cursor_wraps_board_edges(self) -> None:
        state = GameState()
        state.cursor_row = 0
        state.cursor_col = 0
        move_cursor(state, -1, -1)
        self.assertEqual((7, 7), (state.cursor_row, state.cursor_col))

    def test_append_log_keeps_recent_entries(self) -> None:
        state = GameState()
        for index in range(20):
            append_log(state, f"move {index}")
        self.assertEqual(12, len(state.move_log))
        self.assertEqual("move 8", state.move_log[0])
        self.assertEqual("move 19", state.move_log[-1])

    def test_legal_destinations_for_selection_lists_piece_targets(self) -> None:
        state = GameState()
        start_new_game(state)
        state.selected_square = (6, 4)
        destinations = legal_destinations_for_selection(state)
        self.assertIn((5, 4), destinations)
        self.assertIn((4, 4), destinations)

    def test_build_selected_move_text_defaults_promotion_to_queen(self) -> None:
        state = GameState()
        state.position = from_fen("k7/4P3/8/8/8/8/8/4K3 w - - 0 1")
        state.selected_square = (1, 4)
        self.assertEqual("e7e8q", build_selected_move_text(state, 0, 4))

    def test_select_or_play_cursor_square_selects_then_moves(self) -> None:
        state = GameState()
        start_new_game(state)
        state.cursor_row = 6
        state.cursor_col = 4
        select_or_play_cursor_square(state)
        self.assertEqual((6, 4), state.selected_square)

        state.cursor_row = 4
        state.cursor_col = 4
        select_or_play_cursor_square(state)
        self.assertEqual("P", state.position.board[4][4])
        self.assertIsNone(state.selected_square)
        self.assertFalse(state.position.white_to_move)
        self.assertEqual(["New game: Medium", "You: e2e4"], state.move_log)
        self.assertIsNotNone(state.engine_move_due_at)
        self.assertEqual(1, state.pending_engine_reply_ply)

    def test_select_or_play_cursor_square_switches_to_another_piece(self) -> None:
        state = GameState()
        start_new_game(state)
        state.selected_square = (6, 4)
        state.cursor_row = 6
        state.cursor_col = 3
        select_or_play_cursor_square(state)
        self.assertEqual((6, 3), state.selected_square)

    def test_select_or_play_cursor_square_rejects_empty_source(self) -> None:
        state = GameState()
        start_new_game(state)
        state.cursor_row = 4
        state.cursor_col = 4
        select_or_play_cursor_square(state)
        self.assertEqual("Select one of your white pieces first.", state.message)

    def test_clear_selection_resets_choice(self) -> None:
        state = GameState()
        state.selected_square = (6, 4)
        clear_selection(state, "cleared")
        self.assertIsNone(state.selected_square)
        self.assertEqual("cleared", state.message)

    def test_process_command_undo_clears_selection(self) -> None:
        state = GameState()
        start_new_game(state)
        process_command(state, "e2e4")
        state.selected_square = (6, 3)
        process_command(state, "undo")
        self.assertIsNone(state.selected_square)
        self.assertIsNone(state.engine_move_due_at)
        self.assertIsNone(state.pending_engine_reply_ply)

    def test_drive_engine_turn_waits_before_moving(self) -> None:
        state = GameState()
        start_new_game(state)
        process_command(state, "e2e4")

        drive_engine_turn(state)

        self.assertFalse(state.position.white_to_move)
        self.assertTrue(state.thinking)
        self.assertEqual("Engine is thinking...", state.message)

    def test_drive_engine_turn_logs_engine_move_after_delay(self) -> None:
        state = GameState()
        start_new_game(state)
        move = legal_move_from_text(state.position, "e2e4")
        self.assertIsNotNone(move)
        apply_move(state.position, move)
        state.move_log.append("You: e2e4")
        state.thinking = True
        state.pending_engine_reply_ply = len(state.position.history)
        state.engine_move_due_at = time.perf_counter() - 0.01

        drive_engine_turn(state)

        self.assertTrue(state.position.white_to_move)
        self.assertFalse(state.thinking)
        self.assertIsNone(state.engine_move_due_at)
        self.assertIsNone(state.pending_engine_reply_ply)
        self.assertTrue(state.move_log[-1].startswith("Engine: "))

    def test_engine_reply_cannot_fire_twice_for_one_human_move(self) -> None:
        state = GameState()
        start_new_game(state)
        process_command(state, "e2e4")
        state.engine_move_due_at = time.perf_counter() - 0.01

        drive_engine_turn(state)
        first_log = list(state.move_log)
        first_history_len = len(state.position.history)
        drive_engine_turn(state)

        self.assertEqual(first_log, state.move_log)
        self.assertEqual(first_history_len, len(state.position.history))
        self.assertTrue(state.position.white_to_move)

    def test_scripted_game_alternates_user_and_engine_moves(self) -> None:
        state = GameState()
        start_new_game(state)

        for _ in range(5):
            self.assertTrue(state.position.white_to_move)
            human_move = sorted(generate_legal_moves(state.position), key=lambda move: move.uci)[0]
            process_command(state, human_move.uci)
            self.assertFalse(state.position.white_to_move)

            drive_engine_turn(state)
            self.assertFalse(state.position.white_to_move)
            state.engine_move_due_at = time.perf_counter() - 0.01
            drive_engine_turn(state)
            self.assertTrue(state.position.white_to_move)

        played = state.move_log[1:]
        self.assertEqual(10, len(played))
        for index, entry in enumerate(played):
            expected_prefix = "You: " if index % 2 == 0 else "Engine: "
            self.assertTrue(entry.startswith(expected_prefix), played)


if __name__ == "__main__":
    unittest.main()
