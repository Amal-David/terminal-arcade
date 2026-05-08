from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from star_blast.game import (
    ENEMY_SPECS,
    MODE_CAMPAIGN,
    MODE_ENDLESS,
    PLAYER_HEIGHT,
    PLAYER_STRAFE_STEP,
    PLAYER_WIDTH,
    Bullet,
    Enemy,
    GameState,
    STAGES,
    VisualEffect,
    advance_visual_effects,
    advance_campaign_if_needed,
    available_endless_kinds,
    clamp_player_x,
    compute_playfield,
    endless_wave_for_score,
    handle_playing_keys,
    handle_player_hit,
    player_row,
    resolve_collisions,
)
from star_blast.storage import load_scores, save_scores


class FakeAudio:
    def __init__(self) -> None:
        self.events: list[str] = []

    def play(self, sound_name: str) -> None:
        self.events.append(sound_name)


class StarBlastLogicTests(unittest.TestCase):
    def test_clamp_player_x_stays_inside_bounds(self) -> None:
        field_w = PLAYER_WIDTH + 17

        self.assertEqual(0, clamp_player_x(0, -1, field_w))
        self.assertEqual(17, clamp_player_x(17, 1, field_w))
        self.assertEqual(9, clamp_player_x(5, PLAYER_STRAFE_STEP, field_w))

    def test_endless_difficulty_steps_up_with_score(self) -> None:
        self.assertEqual(1, endless_wave_for_score(0))
        self.assertEqual(2, endless_wave_for_score(180))
        self.assertEqual(["debris", "scout"], available_endless_kinds(1))
        self.assertEqual(["debris", "scout", "zigzag"], available_endless_kinds(3))
        self.assertEqual(["debris", "scout", "zigzag", "turret"], available_endless_kinds(5))

    def test_compute_playfield_uses_large_sprite_friendly_size(self) -> None:
        _, _, field_w, field_h = compute_playfield(44, 140)

        self.assertGreaterEqual(field_w, 58)
        self.assertGreaterEqual(field_h, 24)
        self.assertLessEqual(field_w, 88)
        self.assertLessEqual(field_h, 32)

    def test_resolve_collisions_removes_enemy_and_adds_score(self) -> None:
        audio = FakeAudio()
        state = GameState(mode=MODE_ENDLESS, screen="playing", score=0, player_x=4)
        state.enemies = [Enemy(kind="scout", x=12.0, y=5.0, hp=1, width=ENEMY_SPECS["scout"].width)]
        state.bullets = [Bullet(x=13.0, y=6.0, dy=-1.6, friendly=True)]

        resolve_collisions(state, field_w=20, field_h=12, audio=audio)

        self.assertEqual(20, state.score)
        self.assertEqual([], state.enemies)
        self.assertEqual([], state.bullets)
        self.assertEqual(["enemy_blast"], audio.events)
        self.assertEqual("enemy", state.visual_effects[-1].kind)

    def test_handle_player_hit_enters_game_over_on_last_life(self) -> None:
        audio = FakeAudio()
        state = GameState(mode=MODE_ENDLESS, screen="playing", lives=1, player_x=4)

        handle_player_hit(state, field_w=20, field_h=12, audio=audio)

        self.assertEqual(0, state.lives)
        self.assertEqual("gameover", state.screen)
        self.assertEqual("Ship destroyed", state.result_text)
        self.assertEqual(["player_hit"], audio.events)
        self.assertEqual("player", state.visual_effects[-1].kind)
        self.assertGreater(state.screen_shake_frames, 0)
        self.assertGreater(state.hit_flash_frames, 0)

    def test_campaign_advances_to_next_stage_after_boss_defeat(self) -> None:
        state = GameState(mode=MODE_CAMPAIGN, screen="playing", stage_index=0, boss_spawned=True, player_x=4)
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
            player_x=4,
        )
        state.enemies = []

        advance_campaign_if_needed(state)

        self.assertEqual("cleared", state.screen)
        self.assertEqual("Campaign clear", state.result_text)

    def test_player_row_is_near_bottom_of_field(self) -> None:
        self.assertEqual(28 - PLAYER_HEIGHT - 1, player_row(28))

    def test_handle_playing_keys_uses_large_arena_strafe_step(self) -> None:
        state = GameState(mode=MODE_ENDLESS, screen="playing", player_x=18)

        handle_playing_keys(state, [ord("a")], field_w=60, field_h=28)

        self.assertEqual(18 - PLAYER_STRAFE_STEP, state.player_x)

    def test_enemy_specs_use_large_multiline_sprites(self) -> None:
        self.assertGreaterEqual(PLAYER_WIDTH, 12)
        self.assertGreaterEqual(PLAYER_HEIGHT, 5)
        self.assertGreaterEqual(ENEMY_SPECS["debris"].height, 3)
        self.assertGreaterEqual(ENEMY_SPECS["carrier"].width, PLAYER_WIDTH)

    def test_handle_playing_keys_supports_hold_buffer_and_autofire_toggle(self) -> None:
        audio = FakeAudio()
        state = GameState(mode=MODE_ENDLESS, screen="playing", player_x=4)

        handle_playing_keys(state, [ord(" ")], field_w=20, field_h=12, audio=audio)

        self.assertEqual(1, len(state.bullets))
        self.assertEqual(3, state.fire_hold_frames)
        self.assertEqual(["laser"], audio.events)

        state.bullets.clear()
        state.shot_cooldown = 0
        state.fire_hold_frames = 1
        handle_playing_keys(state, [], field_w=20, field_h=12, audio=audio)
        self.assertEqual(1, len(state.bullets))

        state.bullets.clear()
        state.shot_cooldown = 0
        handle_playing_keys(state, [ord("f")], field_w=20, field_h=12, audio=audio)
        self.assertTrue(state.autofire_enabled)
        self.assertEqual(1, len(state.bullets))

    def test_visual_effects_expire_after_duration(self) -> None:
        state = GameState()
        state.visual_effects.append(VisualEffect("enemy", 5, 5, duration=2))

        advance_visual_effects(state)
        self.assertEqual(1, len(state.visual_effects))
        advance_visual_effects(state)
        self.assertEqual([], state.visual_effects)


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
