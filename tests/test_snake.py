"""Tests for the snake game."""

import unittest

from snake_game.game import (
    DOWN,
    LEFT,
    OPPOSITES,
    RIGHT,
    UP,
    GameState,
    move_snake,
    new_game,
    spawn_food,
    update,
)

# Tests use a fixed 30x20 grid (the default)
GW, GH = 30, 20


class TestSnakeMovement(unittest.TestCase):
    def test_move_right(self):
        state = new_game(0, GW, GH)
        state.direction = RIGHT
        state.next_direction = RIGHT
        head_before = state.snake[0]
        move_snake(state)
        hx, hy = state.snake[0]
        self.assertEqual(hx, head_before[0] + 1)
        self.assertEqual(hy, head_before[1])
        self.assertFalse(state.is_dead)

    def test_move_all_directions(self):
        setups = {
            UP: [(10, 10), (10, 11), (10, 12)],
            DOWN: [(10, 10), (10, 9), (10, 8)],
            LEFT: [(10, 10), (11, 10), (12, 10)],
            RIGHT: [(10, 10), (9, 10), (8, 10)],
        }
        for direction, snake in setups.items():
            state = new_game(0, GW, GH)
            state.snake = list(snake)
            state.direction = direction
            state.next_direction = direction
            move_snake(state)
            hx, hy = state.snake[0]
            dx, dy = direction
            self.assertEqual(hx, 10 + dx)
            self.assertEqual(hy, 10 + dy)
            self.assertFalse(state.is_dead, f"Died moving {direction}")

    def test_hits_right_wall(self):
        state = new_game(0, GW, GH)
        state.snake = [(GW - 1, 10), (GW - 2, 10), (GW - 3, 10)]
        state.direction = RIGHT
        state.next_direction = RIGHT
        move_snake(state)
        self.assertTrue(state.is_dead)

    def test_hits_left_wall(self):
        state = new_game(0, GW, GH)
        state.snake = [(0, 10), (1, 10), (2, 10)]
        state.direction = LEFT
        state.next_direction = LEFT
        move_snake(state)
        self.assertTrue(state.is_dead)

    def test_hits_top_wall(self):
        state = new_game(0, GW, GH)
        state.snake = [(10, 0), (10, 1), (10, 2)]
        state.direction = UP
        state.next_direction = UP
        move_snake(state)
        self.assertTrue(state.is_dead)

    def test_hits_bottom_wall(self):
        state = new_game(0, GW, GH)
        state.snake = [(10, GH - 1), (10, GH - 2), (10, GH - 3)]
        state.direction = DOWN
        state.next_direction = DOWN
        move_snake(state)
        self.assertTrue(state.is_dead)


class TestCollision(unittest.TestCase):
    def test_self_collision(self):
        state = new_game(0, GW, GH)
        state.snake = [(5, 5), (6, 5), (6, 6), (5, 6), (4, 6), (4, 5)]
        state.direction = DOWN
        state.next_direction = DOWN
        move_snake(state)
        self.assertTrue(state.is_dead)

    def test_no_collision_normal(self):
        state = new_game(0, GW, GH)
        state.snake = [(10, 10), (9, 10), (8, 10)]
        state.direction = RIGHT
        state.next_direction = RIGHT
        move_snake(state)
        self.assertFalse(state.is_dead)


class TestFood(unittest.TestCase):
    def test_spawn_not_on_snake(self):
        state = new_game(0, GW, GH)
        for _ in range(100):
            food = spawn_food(state)
            self.assertNotIn(food, state.snake)
            self.assertTrue(0 <= food[0] < GW)
            self.assertTrue(0 <= food[1] < GH)

    def test_eating_food_grows_snake(self):
        state = new_game(0, GW, GH)
        state.snake = [(10, 10), (9, 10), (8, 10)]
        state.food = (11, 10)
        state.direction = RIGHT
        state.next_direction = RIGHT
        old_len = len(state.snake)
        move_snake(state)
        self.assertEqual(len(state.snake), old_len + 1)
        self.assertEqual(state.food_eaten, 1)
        self.assertEqual(state.score, 10)

    def test_eating_food_spawns_new(self):
        state = new_game(0, GW, GH)
        state.snake = [(10, 10), (9, 10), (8, 10)]
        old_food = (11, 10)
        state.food = old_food
        state.direction = RIGHT
        state.next_direction = RIGHT
        move_snake(state)
        self.assertNotEqual(state.food, old_food)


class TestDirectionChange(unittest.TestCase):
    def test_opposites_defined(self):
        self.assertEqual(OPPOSITES[UP], DOWN)
        self.assertEqual(OPPOSITES[DOWN], UP)
        self.assertEqual(OPPOSITES[LEFT], RIGHT)
        self.assertEqual(OPPOSITES[RIGHT], LEFT)

    def test_no_reversal(self):
        """The game should not allow 180-degree turns."""
        for direction, opposite in OPPOSITES.items():
            self.assertNotEqual(direction, opposite)


class TestSpeedProgression(unittest.TestCase):
    def test_speed_increases_every_5_food(self):
        state = new_game(0, GW, GH)
        initial_speed = state.speed
        for i in range(5):
            state.snake = [(10, 10), (9, 10), (8, 10)]
            state.food = (11, 10)
            state.direction = RIGHT
            state.next_direction = RIGHT
            move_snake(state)
            state.food = spawn_food(state)
        self.assertGreater(state.speed, initial_speed)


class TestHighScore(unittest.TestCase):
    def test_new_high_score_tracked(self):
        state = new_game(0, GW, GH)
        state.snake = [(10, 10), (9, 10), (8, 10)]
        state.food = (11, 10)
        state.direction = RIGHT
        state.next_direction = RIGHT
        move_snake(state)
        self.assertTrue(state.new_high_score)
        self.assertEqual(state.high_score, 10)

    def test_no_new_high_score_when_below(self):
        state = new_game(1000, GW, GH)
        state.snake = [(10, 10), (9, 10), (8, 10)]
        state.food = (11, 10)
        state.direction = RIGHT
        state.next_direction = RIGHT
        move_snake(state)
        self.assertFalse(state.new_high_score)


class TestGridSizing(unittest.TestCase):
    def test_compute_grid_size_fills_terminal(self):
        from snake_game.game import compute_grid_size
        gw, gh = compute_grid_size(50, 200)
        # Should fill roughly 80% of available space
        self.assertGreater(gw, 50)
        self.assertGreater(gh, 25)

    def test_compute_grid_size_minimum(self):
        from snake_game.game import compute_grid_size
        gw, gh = compute_grid_size(20, 50)
        self.assertGreaterEqual(gw, 15)
        self.assertGreaterEqual(gh, 10)

    def test_new_game_uses_grid_size(self):
        state = new_game(0, 40, 30)
        self.assertEqual(state.grid_w, 40)
        self.assertEqual(state.grid_h, 30)
        # Snake should be centered
        hx, hy = state.snake[0]
        self.assertEqual(hx, 20)
        self.assertEqual(hy, 15)


if __name__ == "__main__":
    unittest.main()
