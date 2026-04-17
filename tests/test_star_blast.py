from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from star_blast.game import (
    MODE_CAMPAIGN,
    MODE_ENDLESS,
    Bullet,
    Enemy,
    GameState,
    STAGES,
    advance_campaign_if_needed,
    available_endless_kinds,
    clamp_player_y,
    endless_wave_for_score,
    handle_player_hit,
    resolve_collisions,
)
from star_blast.storage import load_scores, save_scores


class StarBlastLogicTests(unittest.TestCase):
    def test_clamp_player_y_stays_inside_bounds(self) -> None:
        self.assertEqual(0, clamp_player_y(0, -1, 10))
        self.assertEqual(9, clamp_player_y(9, 1, 10))
        self.assertEqual(5, clamp_player_y(4, 1, 10))

    def test_endless_difficulty_steps_up_with_score(self) -> None:
        self.assertEqual(1, endless_wave_for_score(0))
        self.assertEqual(2, endless_wave_for_score(180))
        self.assertEqual(["debris", "scout"], available_endless_kinds(1))
        self.assertEqual(["debris", "scout", "zigzag"], available_endless_kinds(3))
        self.assertEqual(["debris", "scout", "zigzag", "turret"], available_endless_kinds(5))

    def test_resolve_collisions_removes_enemy_and_adds_score(self) -> None:
        state = GameState(mode=MODE_ENDLESS, screen="playing", score=0, player_y=5)
        state.enemies = [Enemy(kind="scout", x=12.0, y=5, hp=1)]
        state.bullets = [Bullet(x=12.0, y=5, dx=1.6, friendly=True)]

        resolve_collisions(state, field_h=12)

        self.assertEqual(20, state.score)
        self.assertEqual([], state.enemies)
        self.assertEqual([], state.bullets)

    def test_handle_player_hit_enters_game_over_on_last_life(self) -> None:
        state = GameState(mode=MODE_ENDLESS, screen="playing", lives=1, player_y=4)

        handle_player_hit(state, field_h=12)

        self.assertEqual(0, state.lives)
        self.assertEqual("gameover", state.screen)
        self.assertEqual("Ship destroyed", state.result_text)

    def test_campaign_advances_to_next_stage_after_boss_defeat(self) -> None:
        state = GameState(mode=MODE_CAMPAIGN, screen="playing", stage_index=0, boss_spawned=True, player_y=4)
        state.enemies = []

        advance_campaign_if_needed(state)

        self.assertEqual(1, state.stage_index)
        self.assertEqual(0, state.stage_frame)
        self.assertFalse(state.boss_spawned)
        self.assertEqual(f"Stage 2: {STAGES[1].name}", state.banner_text)

    def test_campaign_final_stage_sets_clear_screen(self) -> None:
        state = GameState(
            mode=MODE_CAMPAIGN,
            screen="playing",
            stage_index=len(STAGES) - 1,
            boss_spawned=True,
            player_y=4,
        )
        state.enemies = []

        advance_campaign_if_needed(state)

        self.assertEqual("cleared", state.screen)
        self.assertEqual("Campaign clear", state.result_text)


class StarBlastStorageTests(unittest.TestCase):
    def test_scores_round_trip(self) -> None:
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            self.assertEqual(
                {"campaign_high_score": 0, "endless_high_score": 0},
                load_scores(base_dir),
            )
            save_scores({"campaign_high_score": 240, "endless_high_score": 510}, base_dir)
            self.assertEqual(
                {"campaign_high_score": 240, "endless_high_score": 510},
                load_scores(base_dir),
            )


if __name__ == "__main__":
    unittest.main()
