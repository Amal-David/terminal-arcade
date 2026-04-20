from pathlib import Path
from tempfile import TemporaryDirectory
import random
import unittest

from tetris_game.game import (
    BOARD_H,
    BOARD_W,
    GameState,
    Piece,
    clear_lines,
    empty_board,
    fill_queue,
    gravity_for_level,
    hard_drop,
    make_bag,
    soft_drop,
    spawn_piece,
    start_game,
    try_move,
    try_rotate,
)
from tetris_game.storage import load_high_score, save_high_score


class TetrisLogicTests(unittest.TestCase):
    def test_make_bag_returns_all_seven_pieces(self) -> None:
        bag = make_bag(random.Random(1))
        self.assertEqual(sorted("IOTSZJL"), sorted(bag))
        self.assertEqual(7, len(set(bag)))

    def test_move_clamps_at_left_wall(self) -> None:
        state = GameState(board=empty_board(), current=Piece("J", x=0, y=0))
        self.assertFalse(try_move(state, -1, 0))
        self.assertEqual(0, state.current.x)

    def test_rotate_uses_wall_kick_near_left_edge(self) -> None:
        state = GameState(board=empty_board(), current=Piece("J", rotation=0, x=0, y=0))
        self.assertTrue(try_rotate(state, 1))
        self.assertEqual(1, state.current.rotation)
        self.assertGreaterEqual(state.current.x, 0)

    def test_clear_lines_shifts_rows_down_and_scores_tetris(self) -> None:
        state = GameState(board=empty_board(), level=1)
        state.board[BOARD_H - 1] = ["I"] * BOARD_W
        state.board[BOARD_H - 2] = ["I"] * BOARD_W
        state.board[BOARD_H - 3] = ["I"] * BOARD_W
        state.board[BOARD_H - 4] = ["I"] * BOARD_W
        state.board[BOARD_H - 5][0] = "T"

        cleared = clear_lines(state)

        self.assertEqual(4, cleared)
        self.assertEqual(4, state.lines)
        self.assertEqual(800, state.score)
        self.assertEqual("T", state.board[BOARD_H - 1][0])

    def test_level_increases_every_ten_lines(self) -> None:
        state = GameState(board=empty_board(), level=1, lines=9)
        state.board[BOARD_H - 1] = ["I"] * BOARD_W

        clear_lines(state)

        self.assertEqual(10, state.lines)
        self.assertEqual(2, state.level)
        self.assertGreater(gravity_for_level(2), gravity_for_level(1))

    def test_soft_drop_awards_points_per_row(self) -> None:
        rng = random.Random(1)
        state = GameState(board=empty_board(), current=Piece("I", rotation=1, x=3, y=0), next_kind="O")

        moved = soft_drop(state, rng)

        self.assertTrue(moved)
        self.assertEqual(1, state.score)
        self.assertEqual(1, state.current.y)

    def test_hard_drop_awards_points_and_locks_piece(self) -> None:
        rng = random.Random(1)
        state = GameState(board=empty_board(), current=Piece("O", x=3, y=0), next_kind="I")
        fill_queue(state, rng)

        distance = hard_drop(state, rng)

        self.assertGreater(distance, 0)
        self.assertEqual(distance * 2, state.score)
        self.assertIsNotNone(state.current)
        self.assertTrue(any(cell is not None for row in state.board for cell in row))

    def test_spawn_piece_top_out_sets_failure(self) -> None:
        rng = random.Random(1)
        state = GameState(board=empty_board(), next_kind="O")
        for x in range(BOARD_W):
            state.board[0][x] = "T"
            state.board[1][x] = "T"

        self.assertFalse(spawn_piece(state, rng))

    def test_start_game_initializes_current_and_next_piece(self) -> None:
        rng = random.Random(1)
        state = GameState(high_score=120, board=empty_board())

        start_game(state, rng)

        self.assertTrue(state.started)
        self.assertIsNotNone(state.current)
        self.assertIn(state.current.kind, "IOTSZJL")
        self.assertIn(state.next_kind, "IOTSZJL")


class TetrisStorageTests(unittest.TestCase):
    def test_high_score_round_trip(self) -> None:
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            self.assertEqual(0, load_high_score(base_dir))
            save_high_score(9000, base_dir)
            self.assertEqual(9000, load_high_score(base_dir))


if __name__ == "__main__":
    unittest.main()
