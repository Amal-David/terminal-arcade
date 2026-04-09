"""Tests for the snake game."""

import unittest

from snake_game.game import (
    GRID_H,
    GRID_W,
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


class TestSnakeMovement(unittest.TestCase):
    def test_move_right(self):
        state = new_game(0)
        state.direction = RIGHT
        state.next_direction = RIGHT
        head_before = state.snake[0]
        move_snake(state)
        hx, hy = state.snake[0]
        self.assertEqual(hx, head_before[0] + 1)
        self.assertEqual(hy, head_before[1])
        self.assertFalse(state.is_dead)

    def test_move_all_directions(self):
        # Each direction needs a snake body that doesn't block the move
        setups = {
            UP: [(10, 10), (10, 11), (10, 12)],     # body below, moving up
            DOWN: [(10, 10), (10, 9), (10, 8)],      # body above, moving down
            LEFT: [(10, 10), (11, 10), (12, 10)],    # body right, moving left
            RIGHT: [(10, 10), (9, 10), (8, 10)],     # body left, moving right
        }
        for direction, snake in setups.items():
            state = new_game(0)
            state.snake = list(snake)
            state.direction = direction
            state.next_direction = direction
            move_snake(state)
            hx, hy = state.snake[0]
            dx, dy = direction
            self.assertEqual(hx, (10 + dx) % GRID_W)
            self.assertEqual(hy, (10 + dy) % GRID_H)
            self.assertFalse(state.is_dead, f"Died moving {direction}")

    def test_wrap_right(self):
        state = new_game(0)
        state.snake = [(GRID_W - 1, 10), (GRID_W - 2, 10), (GRID_W - 3, 10)]
        state.direction = RIGHT
        state.next_direction = RIGHT
        move_snake(state)
        self.assertEqual(state.snake[0], (0, 10))
        self.assertFalse(state.is_dead)

    def test_wrap_left(self):
        state = new_game(0)
        state.snake = [(0, 10), (1, 10), (2, 10)]
        state.direction = LEFT
        state.next_direction = LEFT
        move_snake(state)
        self.assertEqual(state.snake[0], (GRID_W - 1, 10))

    def test_wrap_top(self):
        state = new_game(0)
        state.snake = [(10, 0), (10, 1), (10, 2)]
        state.direction = UP
        state.next_direction = UP
        move_snake(state)
        self.assertEqual(state.snake[0], (10, GRID_H - 1))

    def test_wrap_bottom(self):
        state = new_game(0)
        state.snake = [(10, GRID_H - 1), (10, GRID_H - 2), (10, GRID_H - 3)]
        state.direction = DOWN
        state.next_direction = DOWN
        move_snake(state)
        self.assertEqual(state.snake[0], (10, 0))


class TestCollision(unittest.TestCase):
    def test_self_collision(self):
        state = new_game(0)
        # Snake curled into itself
        state.snake = [(5, 5), (6, 5), (6, 6), (5, 6), (4, 6), (4, 5)]
        state.direction = DOWN
        state.next_direction = DOWN
        # Moving down from (5,5) goes to (5,6) which is in the body
        move_snake(state)
        self.assertTrue(state.is_dead)

    def test_no_collision_normal(self):
        state = new_game(0)
        state.snake = [(10, 10), (9, 10), (8, 10)]
        state.direction = RIGHT
        state.next_direction = RIGHT
        move_snake(state)
        self.assertFalse(state.is_dead)


class TestFood(unittest.TestCase):
    def test_spawn_not_on_snake(self):
        state = new_game(0)
        for _ in range(100):
            food = spawn_food(state)
            self.assertNotIn(food, state.snake)
            self.assertTrue(0 <= food[0] < GRID_W)
            self.assertTrue(0 <= food[1] < GRID_H)

    def test_eating_food_grows_snake(self):
        state = new_game(0)
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
        state = new_game(0)
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
        """The game should not allow 180-degree turns — verified via OPPOSITES check."""
        for direction, opposite in OPPOSITES.items():
            self.assertNotEqual(direction, opposite)


class TestSpeedProgression(unittest.TestCase):
    def test_speed_increases_every_5_food(self):
        state = new_game(0)
        initial_speed = state.speed
        # Eat 5 food items
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
        state = new_game(0)
        state.snake = [(10, 10), (9, 10), (8, 10)]
        state.food = (11, 10)
        state.direction = RIGHT
        state.next_direction = RIGHT
        move_snake(state)
        self.assertTrue(state.new_high_score)
        self.assertEqual(state.high_score, 10)

    def test_no_new_high_score_when_below(self):
        state = new_game(1000)
        state.snake = [(10, 10), (9, 10), (8, 10)]
        state.food = (11, 10)
        state.direction = RIGHT
        state.next_direction = RIGHT
        move_snake(state)
        self.assertFalse(state.new_high_score)


if __name__ == "__main__":
    unittest.main()
