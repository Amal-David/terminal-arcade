import random
import unittest

from dino_game.assets import DINOSAUR_FRAMES, DINOSAUR_ORDER
from dino_game.generated_svg_frames import SVG_TYRANT_FRAMES
from dino_game.game import (
    GameState,
    Obstacle,
    PATTERN_TEMPLATES,
    ROAR_CHARGE_MAX,
    apply_roar_hits,
    available_patterns,
    biome_for_score,
    choose_dinosaur,
    choose_pattern,
    cycle_dinosaur,
    selected_dinosaur_key,
    speed_target,
    trigger_roar,
)


class GameplayTests(unittest.TestCase):
    def test_biome_rotation_cycles_every_300_score(self) -> None:
        self.assertEqual("scrub", biome_for_score(0))
        self.assertEqual("scrub", biome_for_score(299))
        self.assertEqual("fossil", biome_for_score(300))
        self.assertEqual("basalt", biome_for_score(600))
        self.assertEqual("scrub", biome_for_score(900))

    def test_speed_target_is_monotonic(self) -> None:
        checkpoints = [0, 150, 300, 600, 900, 1200]
        speeds = [speed_target(score) for score in checkpoints]
        self.assertEqual(sorted(speeds), speeds)
        self.assertGreater(speeds[-1], speeds[0])

    def test_each_biome_has_multiple_patterns(self) -> None:
        for biome, speed in [("scrub", 2.6), ("fossil", 3.1), ("basalt", 3.8)]:
            patterns = available_patterns(biome, speed)
            self.assertGreaterEqual(len(patterns), 4, biome)

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
            Obstacle(x=18, hazard_name="desert_pad", biome="scrub"),
            Obstacle(x=20, hazard_name="desert_tall", biome="scrub"),
            Obstacle(x=45, hazard_name="desert_stump", biome="scrub"),
        ]

        destroyed = apply_roar_hits(state, frame_count=0)

        self.assertEqual(1, destroyed)
        self.assertEqual(["desert_tall", "desert_stump"], [o.hazard_name for o in state.obstacles])

    def test_pattern_groups_never_exceed_two(self) -> None:
        self.assertTrue(all(pattern.group_size <= 2 for pattern in PATTERN_TEMPLATES))

    def test_pattern_selection_avoids_triple_repeat(self) -> None:
        history: list[str] = []
        rng = random.Random(42)
        for _ in range(300):
            choice = choose_pattern("scrub", 2.8, history, rng)
            history.append(choice.name)
            if len(history) >= 3:
                self.assertFalse(history[-1] == history[-2] == history[-3])

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
