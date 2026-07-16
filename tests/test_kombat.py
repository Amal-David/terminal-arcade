import random
import unittest
from unittest.mock import patch

import kombat_game.game as kombat


class FakeScreen:
    def __init__(self, height: int = 44, width: int = 132) -> None:
        self.height = height
        self.width = width
        self.drawn: list[str] = []

    def getmaxyx(self) -> tuple[int, int]:
        return self.height, self.width

    def erase(self) -> None:
        self.drawn.clear()

    def addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        self.drawn.append(text)

    def refresh(self) -> None:
        pass


class TerminalKombatRulesTests(unittest.TestCase):
    def test_roster_has_distinct_original_fighters(self) -> None:
        roster = kombat.build_roster()

        self.assertEqual(["volt", "nyx", "kade"], [fighter.id for fighter in roster])
        self.assertEqual(len({fighter.special_name for fighter in roster}), 3)
        self.assertTrue(all(kombat.sprite_height(fighter.animations["idle"]) >= 18 for fighter in roster))
        self.assertTrue(all(kombat.sprite_width(fighter.animations["punch"]) >= 40 for fighter in roster))
        self.assertTrue(all(fighter.max_health > 0 for fighter in roster))

    def test_sprites_have_human_anatomy_markers(self) -> None:
        volt = kombat.build_roster()[0]
        idle = "\n".join(volt.animations["idle"])

        self.assertIn("/  o  o  \\", idle)
        self.assertIn("|VOLT|", idle)
        self.assertIn("O O", idle)
        self.assertIn("/___\\        /___\\", idle)

        for action, sprite in volt.animations.items():
            text = "\n".join(sprite)
            with self.subTest(action=action):
                self.assertGreaterEqual(kombat.sprite_height(sprite), 18)
                self.assertGreaterEqual(kombat.sprite_width(sprite), 38)
                self.assertIn("VOLT", text)
                self.assertIn("O", text)

        self.assertIn("________________O", "\n".join(volt.animations["punch"]))
        self.assertIn("==========O", "\n".join(volt.animations["kick"]))
        self.assertNotEqual(volt.animations["punch"], volt.animations["kick"])

    def test_new_match_sets_up_best_of_three_round(self) -> None:
        state = kombat.new_match(player_index=2)

        self.assertEqual("Kade", state.player.spec.name)
        self.assertEqual("Volt", state.enemy.spec.name)
        self.assertEqual("playing", state.phase)
        self.assertEqual(1, state.round_number)
        self.assertLess(state.player.x, state.enemy.x)

    def test_punch_in_range_deals_damage_and_builds_meter(self) -> None:
        state = kombat.new_match()
        state.player.x = 20
        state.enemy.x = 24
        starting_health = state.enemy.health

        self.assertTrue(kombat.start_attack(state, "player", "punch"))

        self.assertLess(state.enemy.health, starting_health)
        self.assertGreater(state.player.meter, 0)
        self.assertEqual("hit", state.enemy.action)

    def test_block_reduces_incoming_damage_and_builds_defender_meter(self) -> None:
        unblocked = kombat.new_match()
        unblocked.player.x = 20
        unblocked.enemy.x = 24
        kombat.start_attack(unblocked, "player", "kick")
        unblocked_damage = unblocked.enemy.spec.max_health - unblocked.enemy.health

        blocked = kombat.new_match()
        blocked.player.x = 20
        blocked.enemy.x = 24
        self.assertTrue(kombat.start_block(blocked, "enemy"))
        kombat.tick_fighter(blocked.enemy)
        self.assertTrue(kombat.start_attack(blocked, "player", "kick"))
        blocked_damage = blocked.enemy.spec.max_health - blocked.enemy.health

        self.assertLess(blocked_damage, unblocked_damage)
        self.assertGreater(blocked.enemy.meter, 0)

    def test_special_requires_and_consumes_meter(self) -> None:
        state = kombat.new_match()
        state.player.x = 20
        state.enemy.x = 34

        self.assertFalse(kombat.start_attack(state, "player", "special"))
        state.player.meter = kombat.ATTACKS["special"].meter_cost
        self.assertTrue(kombat.start_attack(state, "player", "special"))

        self.assertEqual(0, state.player.meter)
        self.assertLess(state.enemy.health, state.enemy.spec.max_health)

    def test_expanded_actions_include_crouch_jump_throw_sweep_and_finisher(self) -> None:
        state = kombat.new_match()
        state.player.x = 20
        state.enemy.x = 35

        self.assertTrue(kombat.start_crouch(state, "player"))
        self.assertEqual("crouch", state.player.action)
        for _ in range(10):
            kombat.tick_fighter(state.player)

        self.assertTrue(kombat.start_jump(state, "player"))
        self.assertEqual("jump", state.player.action)
        kombat.tick_fighter(state.player)
        self.assertGreaterEqual(state.player.y_offset, 0)
        for _ in range(kombat.JUMP_FRAMES + 1):
            kombat.tick_fighter(state.player)

        self.assertTrue(kombat.start_attack(state, "player", "sweep"))
        self.assertEqual("sweep", state.player.action)
        for _ in range(kombat.ATTACKS["sweep"].frames + kombat.ATTACKS["sweep"].cooldown):
            kombat.tick_fighter(state.player)

        state.enemy.x = state.player.x + 5
        self.assertTrue(kombat.start_attack(state, "player", "throw"))
        self.assertLess(state.enemy.health, state.enemy.spec.max_health)
        for _ in range(kombat.ATTACKS["throw"].frames + kombat.ATTACKS["throw"].cooldown):
            kombat.tick_fighter(state.player)

        state.enemy.health = kombat.FINISHER_HEALTH
        state.player.meter = kombat.ATTACKS["finisher"].meter_cost
        self.assertTrue(kombat.start_attack(state, "player", "finisher"))
        self.assertEqual("finisher", state.player.action)

    def test_round_and_match_end_when_fighter_is_knocked_out(self) -> None:
        state = kombat.new_match()
        state.player.x = 20
        state.enemy.x = 24
        state.enemy.health = 1

        kombat.start_attack(state, "player", "punch")

        self.assertEqual("round_over", state.phase)
        self.assertEqual(1, state.player.wins)
        self.assertTrue(kombat.start_next_round(state))
        self.assertEqual("playing", state.phase)

        state.enemy.health = 1
        state.player.x = 20
        state.enemy.x = 24
        kombat.start_attack(state, "player", "punch")

        self.assertEqual("match_over", state.phase)
        self.assertEqual("player", state.match_winner)

    def test_cpu_advances_when_out_of_range(self) -> None:
        state = kombat.new_match()
        state.player.x = 15
        state.enemy.x = 80

        action = kombat.choose_cpu_action(state, random.Random(1))
        moved = kombat.apply_cpu_action(state, action)

        self.assertEqual("advance", action)
        self.assertTrue(moved)
        self.assertLess(state.enemy.x, 80)

    def test_cpu_can_choose_richer_close_range_actions(self) -> None:
        state = kombat.new_match()
        state.player.x = 30
        state.enemy.x = 37

        actions = {kombat.choose_cpu_action(state, random.Random(seed)) for seed in range(20)}

        self.assertTrue(actions & {"throw", "low_kick", "kick", "heavy", "sweep", "punch"})

    def test_title_and_game_render_without_curses_colors(self) -> None:
        title_screen = FakeScreen()
        kombat.render_title(title_screen, 0, kombat.build_roster(), has_color=False)

        self.assertTrue(any("Volt" in text for text in title_screen.drawn))
        self.assertTrue(any("Enter/Space fight" in text for text in title_screen.drawn))

        game_screen = FakeScreen()
        state = kombat.new_match()
        kombat.render_game(game_screen, state, has_color=False)

        self.assertTrue(any("ROUND 1" in text for text in game_screen.drawn))
        self.assertTrue(any("A/D move" in text for text in game_screen.drawn))

    def test_run_wraps_curses_main(self) -> None:
        with patch("kombat_game.game.curses.wrapper") as wrapper:
            kombat.run()

        wrapper.assert_called_once_with(kombat.main)


if __name__ == "__main__":
    unittest.main()
