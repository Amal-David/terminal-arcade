import random
import unittest

from dino_game.assets import DINOSAUR_FRAMES, DINOSAUR_ORDER
from dino_game.generated_svg_frames import SVG_TYRANT_FRAMES
from dino_game.game import (
    CLEAR_TIME_FRAMES,
    FAMILY_FLYER,
    FAMILY_GROUND_LARGE,
    FAMILY_GROUND_SMALL,
    FLYER_BASE_MIN_GAP,
    FLYER_MIN_SPEED,
    GAP_COEFFICIENT,
    GROUND_BASE_MIN_GAP,
    GROUND_LARGE_GROUP_MIN_SPEED,
    INITIAL_SPEED,
    MAX_GROUP_SIZE,
    MAX_GAP_COEFFICIENT,
    ROAR_CHARGE_MAX,
    SPEED_ACCELERATION,
    DINO_X,
    ROAR_RANGE,
    GameState,
    Obstacle,
    SpawnGroup,
    apply_roar_hits,
    available_families,
    biome_for_score,
    choose_dinosaur,
    choose_group_size,
    choose_spawn_family,
    choose_spawn_group,
    cycle_dinosaur,
    group_render_width,
    hazard_width,
    sample_group_gap,
    selected_dinosaur_key,
    spawn_obstacle_group,
    trigger_roar,
    update_difficulty,
    update_obstacles,
)


class SilentAudio:
    def play(self, _name: str) -> None:
        pass


class GameplayTests(unittest.TestCase):
    def test_biome_rotation_cycles_every_300_score(self) -> None:
        self.assertEqual("scrub", biome_for_score(0))
        self.assertEqual("scrub", biome_for_score(299))
        self.assertEqual("fossil", biome_for_score(300))
        self.assertEqual("basalt", biome_for_score(600))
        self.assertEqual("scrub", biome_for_score(900))

    def test_speed_acceleration_is_smooth(self) -> None:
        state = GameState(speed=INITIAL_SPEED)
        audio = SilentAudio()

        speeds = []
        for _ in range(8):
            update_difficulty(state, audio)
            speeds.append(state.speed)

        increments = [round(curr - prev, 6) for prev, curr in zip([INITIAL_SPEED] + speeds[:-1], speeds)]
        self.assertTrue(all(increment == round(SPEED_ACCELERATION, 6) for increment in increments))

    def test_flyer_family_unlocks_at_target_speed(self) -> None:
        self.assertNotIn(FAMILY_FLYER, available_families(FLYER_MIN_SPEED - 0.01))
        self.assertIn(FAMILY_FLYER, available_families(FLYER_MIN_SPEED))

    def test_ground_large_groups_unlock_at_target_speed(self) -> None:
        low_rng = random.Random(7)
        self.assertTrue(
            all(choose_group_size(FAMILY_GROUND_LARGE, GROUND_LARGE_GROUP_MIN_SPEED - 0.01, low_rng) == 1 for _ in range(20))
        )

        high_rng = random.Random(7)
        self.assertTrue(
            any(choose_group_size(FAMILY_GROUND_LARGE, GROUND_LARGE_GROUP_MIN_SPEED, high_rng) > 1 for _ in range(50))
        )

    def test_spawn_family_never_repeats_three_times(self) -> None:
        history: list[str] = []
        rng = random.Random(42)

        for _ in range(300):
            family = choose_spawn_family(FLYER_MIN_SPEED + 0.6, history, rng)
            history.append(family)
            if len(history) >= 3:
                self.assertFalse(history[-1] == history[-2] == history[-3])

    def test_spawn_family_never_places_flyer_after_flyer(self) -> None:
        rng = random.Random(9)
        for _ in range(100):
            self.assertNotEqual(FAMILY_FLYER, choose_spawn_family(FLYER_MIN_SPEED + 0.5, [FAMILY_FLYER], rng))

    def test_sampled_gap_varies_within_bounds(self) -> None:
        rng = random.Random(11)
        values = [sample_group_gap(FAMILY_GROUND_SMALL, "desert_pad", 2, 2.5, rng) for _ in range(40)]
        min_gap = round(group_render_width("desert_pad", 2) * 2.5 + GROUND_BASE_MIN_GAP * GAP_COEFFICIENT)
        max_gap = round(min_gap * MAX_GAP_COEFFICIENT)

        self.assertGreater(len(set(values)), 1)
        self.assertTrue(all(min_gap <= value <= max_gap for value in values))

    def test_flyer_gap_uses_flyer_base_gap(self) -> None:
        rng = random.Random(5)
        value = sample_group_gap(FAMILY_FLYER, "scavenger", 1, 3.2, rng)
        min_gap = round(group_render_width("scavenger", 1) * 3.2 + FLYER_BASE_MIN_GAP * GAP_COEFFICIENT)
        max_gap = round(min_gap * MAX_GAP_COEFFICIENT)
        self.assertGreaterEqual(value, min_gap)
        self.assertLessEqual(value, max_gap)

    def test_no_obstacles_spawn_during_clear_time(self) -> None:
        state = GameState(started=True, current_biome="scrub")
        rng = random.Random(3)

        for frame in range(CLEAR_TIME_FRAMES):
            state.running_frames = frame
            update_obstacles(state, 80, rng)
            self.assertEqual([], state.obstacles)

        state.running_frames = CLEAR_TIME_FRAMES
        update_obstacles(state, 80, rng)
        self.assertTrue(state.obstacles)

    def test_spawned_group_uses_spacing_and_starts_offscreen(self) -> None:
        state = GameState(started=True, current_biome="scrub", speed=2.8)
        rng = random.Random(1)
        group = SpawnGroup(
            family=FAMILY_GROUND_SMALL,
            hazard_name="desert_pad",
            group_size=MAX_GROUP_SIZE,
            gap_after=24,
        )

        spawn_obstacle_group(state, 80, rng, group)

        self.assertEqual(MAX_GROUP_SIZE, len(state.obstacles))
        self.assertTrue(all(obstacle.x >= 80 for obstacle in state.obstacles))

        width = hazard_width("desert_pad")
        for previous, current in zip(state.obstacles, state.obstacles[1:]):
            self.assertEqual(previous.x + width + 1, current.x)

    def test_spawned_group_stays_outside_reaction_window(self) -> None:
        state = GameState(started=True, current_biome="scrub", speed=2.8)
        rng = random.Random(4)
        group = SpawnGroup(
            family=FAMILY_GROUND_LARGE,
            hazard_name="desert_tall",
            group_size=2,
            gap_after=30,
        )

        spawn_obstacle_group(state, 80, rng, group)

        self.assertTrue(all(obstacle.x > DINO_X + ROAR_RANGE for obstacle in state.obstacles))

    def test_choose_spawn_group_can_emit_flyer_after_unlock(self) -> None:
        rng = random.Random(12)
        groups = [choose_spawn_group("basalt", FLYER_MIN_SPEED + 0.4, [], rng).family for _ in range(120)]
        self.assertIn(FAMILY_FLYER, groups)

    def test_roar_requires_full_charge(self) -> None:
        state = GameState(roar_charge=ROAR_CHARGE_MAX - 1)
        self.assertFalse(trigger_roar(state))
        state.roar_charge = ROAR_CHARGE_MAX
        self.assertTrue(trigger_roar(state))
        self.assertEqual(0.0, state.roar_charge)
        self.assertGreater(state.roar_timer, 0)

    def test_roar_clears_only_fragile_hazards_in_range(self) -> None:
        state = GameState(roar_charge=ROAR_CHARGE_MAX)
        trigger_roar(state)
        state.obstacles = [
            Obstacle(x=18, hazard_name="desert_pad", biome="scrub", family=FAMILY_GROUND_SMALL, group_id=0),
            Obstacle(x=20, hazard_name="desert_tall", biome="scrub", family=FAMILY_GROUND_LARGE, group_id=1),
            Obstacle(x=45, hazard_name="desert_stump", biome="scrub", family=FAMILY_GROUND_SMALL, group_id=2),
        ]

        destroyed = apply_roar_hits(state, frame_count=0)

        self.assertEqual(1, destroyed)
        self.assertEqual(["desert_tall", "desert_stump"], [o.hazard_name for o in state.obstacles])

    def test_roster_has_ten_dinosaur_options(self) -> None:
        self.assertEqual(10, len(DINOSAUR_ORDER))

    def test_each_dinosaur_has_full_animation_set(self) -> None:
        required_states = {"idle", "run", "jump_up", "apex", "fall", "duck", "hit", "roar"}
        for key, frames in DINOSAUR_FRAMES.items():
            self.assertEqual(required_states, set(frames), key)
            self.assertEqual(2, len(frames["idle"]), key)
            self.assertEqual(6, len(frames["run"]), key)
            self.assertEqual(2, len(frames["duck"]), key)
            self.assertEqual(3, len(frames["roar"]), key)

    def test_default_tyrant_frames_come_from_generated_svg_pipeline(self) -> None:
        self.assertEqual(SVG_TYRANT_FRAMES, DINOSAUR_FRAMES["tyrant"])

    def test_selection_wraps_across_roster(self) -> None:
        state = GameState(selected_dino=DINOSAUR_ORDER[0])
        self.assertTrue(cycle_dinosaur(state, -1))
        self.assertEqual(DINOSAUR_ORDER[-1], selected_dinosaur_key(state))
        self.assertTrue(choose_dinosaur(state, 0))
        self.assertEqual(DINOSAUR_ORDER[0], selected_dinosaur_key(state))
