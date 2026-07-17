"""Terminal Kombat - a large-sprite original terminal fighting game."""

from __future__ import annotations

import curses
import math
import random
import time
from dataclasses import dataclass
from typing import Literal

from terminal_arcade.ui import hide_cursor, safe_addstr

FPS = 20
FRAME_TIME = 1.0 / FPS
MAX_CATCH_UP_STEPS = 5

MIN_WIDTH = 118
MIN_HEIGHT = 38
ARENA_WIDTH = 100
MIN_FIGHTER_GAP = 18
ROUND_SECONDS = 70
ROUND_FRAMES = ROUND_SECONDS * FPS
METER_MAX = 100
ROUNDS_TO_WIN = 2
COMBO_WINDOW_FRAMES = 26
FINISHER_HEALTH = 18
JUMP_FRAMES = 18

Action = Literal[
    "idle",
    "walk",
    "crouch",
    "jump",
    "punch",
    "kick",
    "low_kick",
    "heavy",
    "sweep",
    "throw",
    "block",
    "special",
    "finisher",
    "hit",
    "ko",
    "victory",
]
Phase = Literal["playing", "paused", "round_over", "match_over"]
Side = Literal["player", "enemy"]
AttackName = Literal["punch", "kick", "low_kick", "heavy", "sweep", "throw", "special", "finisher"]

MOVE_LEFT_KEYS = {curses.KEY_LEFT, ord("a"), ord("A")}
MOVE_RIGHT_KEYS = {curses.KEY_RIGHT, ord("d"), ord("D")}
JUMP_KEYS = {curses.KEY_UP, ord("w"), ord("W")}
CROUCH_KEYS = {curses.KEY_DOWN, ord("s"), ord("S")}
PUNCH_KEYS = {ord("j"), ord("J")}
KICK_KEYS = {ord("k"), ord("K")}
LOW_KICK_KEYS = {ord("u"), ord("U")}
HEAVY_KEYS = {ord("o"), ord("O")}
SWEEP_KEYS = {ord("h"), ord("H")}
THROW_KEYS = {ord(";"), ord(":")}
BLOCK_KEYS = {ord("l"), ord("L")}
SPECIAL_KEYS = {ord("i"), ord("I")}
FINISHER_KEYS = {ord("f"), ord("F")}
PAUSE_KEYS = {ord("p"), ord("P")}
RESTART_KEYS = {ord("r"), ord("R")}
CONFIRM_KEYS = {curses.KEY_ENTER, 10, 13, ord(" ")}
QUIT_KEYS = {ord("q"), ord("Q"), 27}

TITLE_ART = [
    "████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗ █████╗ ██╗",
    "╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗██║",
    "   ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║███████║██║",
    "   ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║",
    "   ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██║  ██║███████╗",
    "   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝",
]

MIRROR_TABLE = str.maketrans(
    {
        "/": "\\",
        "\\": "/",
        "(": ")",
        ")": "(",
        "[": "]",
        "]": "[",
        "{": "}",
        "}": "{",
        "<": ">",
        ">": "<",
        "╱": "╲",
        "╲": "╱",
        "▌": "▐",
        "▐": "▌",
        "◢": "◣",
        "◣": "◢",
        "◤": "◥",
        "◥": "◤",
    }
)


@dataclass(frozen=True)
class AttackSpec:
    action: AttackName
    label: str
    damage: int
    reach: int
    frames: int
    cooldown: int
    meter_gain: int
    meter_cost: int = 0
    stun: int = 8
    knockback: int = 2
    unblockable: bool = False
    requires_finisher_window: bool = False


@dataclass(frozen=True)
class FighterSpec:
    id: str
    name: str
    style: str
    max_health: int
    speed: int
    reach_bonus: int
    special_name: str
    finisher_name: str
    palette: int
    animations: dict[Action, tuple[str, ...]]


@dataclass
class FighterState:
    spec: FighterSpec
    x: int
    facing: int
    health: int
    meter: int = 0
    wins: int = 0
    action: Action = "idle"
    action_timer: int = 0
    cooldown: int = 0
    hit_stun: int = 0
    block_timer: int = 0
    combo: int = 0
    combo_timer: int = 0
    y_offset: int = 0


@dataclass
class VisualEffect:
    kind: str
    x: int
    y: int
    age: int = 0
    duration: int = 10


@dataclass
class CombatState:
    roster: tuple[FighterSpec, ...]
    player: FighterState
    enemy: FighterState
    arena_width: int = ARENA_WIDTH
    round_number: int = 1
    round_frames_left: int = ROUND_FRAMES
    phase: Phase = "playing"
    message: str = "Round 1 - FIGHT!"
    message_timer: int = FPS * 2
    player_score: int = 0
    last_winner: Side | None = None
    match_winner: Side | None = None
    effects: list[VisualEffect] | None = None
    running: bool = True


ATTACKS: dict[AttackName, AttackSpec] = {
    "punch": AttackSpec("punch", "straight punch", 8, 12, 7, 5, 8, stun=7, knockback=1),
    "kick": AttackSpec("kick", "snap kick", 12, 14, 9, 8, 11, stun=8, knockback=2),
    "low_kick": AttackSpec("low_kick", "low kick", 9, 13, 8, 7, 9, stun=9, knockback=1),
    "heavy": AttackSpec("heavy", "heavy strike", 18, 12, 12, 13, 14, stun=11, knockback=3),
    "sweep": AttackSpec("sweep", "leg sweep", 10, 15, 11, 12, 10, stun=15, knockback=4),
    "throw": AttackSpec("throw", "clinch throw", 16, 6, 10, 14, 12, stun=12, knockback=6, unblockable=True),
    "special": AttackSpec("special", "special", 25, 22, 14, 18, 0, meter_cost=45, stun=13, knockback=5),
    "finisher": AttackSpec(
        "finisher",
        "finisher",
        42,
        18,
        20,
        24,
        0,
        meter_cost=70,
        stun=18,
        knockback=7,
        unblockable=True,
        requires_finisher_window=True,
    ),
}


def _pad(sprite: tuple[str, ...]) -> tuple[str, ...]:
    width = max(len(line) for line in sprite)
    return tuple(line.ljust(width) for line in sprite)


def _variant(sprite: tuple[str, ...], replacements: dict[str, str]) -> tuple[str, ...]:
    lines = []
    for line in sprite:
        for old, new in replacements.items():
            line = line.replace(old, new)
        lines.append(line)
    return _pad(tuple(lines))


def _hero_scale(sprite: tuple[str, ...]) -> tuple[str, ...]:
    painted_rows = [index for index, line in enumerate(sprite) if line.strip()]
    if len(painted_rows) < 4:
        return sprite
    first, last = painted_rows[0], painted_rows[-1]
    span = last - first
    if span < 8:
        upper = min(last, first + 1)
        lower = max(first, last - 1)
    else:
        upper = min(last, first + max(5, span // 3))
        lower = max(first, last - max(2, span // 4))
    scaled = list(sprite[: upper + 1])
    scaled.append(sprite[upper])
    scaled.extend(sprite[upper + 1 : lower + 1])
    scaled.append(sprite[lower])
    scaled.extend(sprite[lower + 1 :])
    return _pad(tuple(scaled))


BASE_IDLE = _pad(
    (
        "              .------.              ",
        "             /  FACE  \\             ",
        "            |    __    |            ",
        "             \\  \\__/  /             ",
        "              '.___.'               ",
        "            ___/|__|\\___            ",
        "         __/   /|MARK|\\   \\__       ",
        "        /  ___/ |____| \\___  \\      ",
        "       |  /     |____|     \\  |     ",
        "       | |     /|____|\\     | |     ",
        "       O O    / /    \\ \\    O O     ",
        "             /_/      \\_\\           ",
        "            /  /      \\  \\          ",
        "           /__/        \\__\\         ",
        "          /___\\        /___\\        ",
        "                                      ",
    )
)

BASE_WALK = _pad(
    (
        "              .------.              ",
        "             /  FACE  \\             ",
        "            |    __    |            ",
        "             \\  \\__/  /             ",
        "              '.___.'               ",
        "          ____/|__|\\____            ",
        "       __/   /|MARK|\\   \\__         ",
        "      O  ___/ |____| \\___  O        ",
        "          /   |____|   \\            ",
        "         /   /|____|\\   \\           ",
        "        O   / /    \\ \\   O          ",
        "           /_/      \\ \\             ",
        "          /  /       \\ \\__          ",
        "         /__/         \\___\\         ",
        "        /___\\                       ",
        "                                      ",
    )
)

BASE_CROUCH = _pad(
    (
        "                                      ",
        "                                      ",
        "              .------.              ",
        "             /  FACE  \\             ",
        "            |    __    |            ",
        "             \\  \\__/  /             ",
        "          ____/|__|\\____            ",
        "       __/   /|MARK|\\   \\__         ",
        "      O  ___/ |____| \\___  O        ",
        "       \\_\\  __|____|__  /_/         ",
        "         \\__/  /    \\  \\__/         ",
        "          /___/      \\___\\          ",
        "         /___\\        /___\\         ",
        "                                      ",
        "                                      ",
        "                                      ",
    )
)

BASE_JUMP = _pad(
    (
        "        O\\      .------.      /O     ",
        "          \\    /  FACE  \\    /       ",
        "           \\  |    __    |  /        ",
        "            \\  \\  \\__/  /  /         ",
        "             \\__'.___.'__/          ",
        "                /|__|\\              ",
        "               /|MARK|\\             ",
        "              / |____| \\            ",
        "             /  |____|  \\           ",
        "            O  /|____|\\  O          ",
        "              /_/    \\_\\            ",
        "             /  /    \\  \\           ",
        "            /__/      \\__\\          ",
        "                                      ",
        "                                      ",
        "                                      ",
    )
)

BASE_PUNCH = _pad(
    (
        "              .------.                    ",
        "             /  FACE  \\                   ",
        "            |    __    |                  ",
        "             \\  \\__/  /                   ",
        "              '.___.'                     ",
        "            ___/|__|\\________________O    ",
        "         __/   /|MARK|\\                   ",
        "        /  ___/ |____| \\                  ",
        "       O  /     |____|                    ",
        "          |    /|____|\\                   ",
        "          O   / /    \\ \\                  ",
        "             /_/      \\_\\                 ",
        "            /  /      \\  \\                ",
        "           /__/        \\__\\               ",
        "          /___\\        /___\\              ",
        "                                            ",
    )
)

BASE_KICK = _pad(
    (
        "              .------.                    ",
        "             /  FACE  \\                   ",
        "            |    __    |                  ",
        "             \\  \\__/  /                   ",
        "              '.___.'                     ",
        "            ___/|__|\\___                  ",
        "         __/   /|MARK|\\   \\__             ",
        "        /  ___/ |____| \\___  \\            ",
        "       O  /     |____|     \\  O           ",
        "          |    /|____|\\                   ",
        "          O   / /    \\ \\==========O       ",
        "             /_/      \\                   ",
        "            /  /                           ",
        "           /__/                            ",
        "          /___\\                            ",
        "                                            ",
    )
)

BASE_LOW_KICK = _pad(
    (
        "                                      ",
        "                                      ",
        "              .------.              ",
        "             /  FACE  \\             ",
        "            |    __    |            ",
        "             \\  \\__/  /             ",
        "          ____/|__|\\____            ",
        "       __/   /|MARK|\\   \\__         ",
        "      O  ___/ |____| \\___  O        ",
        "       \\_\\  __|____|__  /_/         ",
        "         \\__/  /    \\==============O",
        "          /___/                       ",
        "         /___\\                        ",
        "                                      ",
        "                                      ",
        "                                      ",
    )
)

BASE_HEAVY = _pad(
    (
        "                         O          ",
        "                        /           ",
        "              .------. /            ",
        "             /  FACE  /             ",
        "            |    __  / |            ",
        "             \\  \\__/  /             ",
        "              '.___.'               ",
        "            ___/|__|\\___            ",
        "         __/   /|MARK|\\   \\__       ",
        "        /  ___/ |____| \\___  \\      ",
        "       O  /    /|____|\\     O       ",
        "             /_/      \\_\\           ",
        "            /  /      \\  \\          ",
        "           /__/        \\__\\         ",
        "          /___\\        /___\\        ",
        "                                      ",
    )
)

BASE_SWEEP = _pad(
    (
        "                                      ",
        "                                      ",
        "              .------.              ",
        "             /  FACE  \\             ",
        "            |    __    |            ",
        "             \\  \\__/  /             ",
        "          ____/|__|\\____            ",
        "       __/   /|MARK|\\   \\__         ",
        "      O  ___/ |____| \\___  O        ",
        "       \\_\\  __|____|__  /_/         ",
        "         \\__/  /    \\  \\__/         ",
        "          /___/      \\==========O   ",
        "         /___\\                       ",
        "                                      ",
        "                                      ",
        "                                      ",
    )
)

BASE_THROW = _pad(
    (
        "              .------.                 ",
        "             /  FACE  \\                ",
        "            |    __    |               ",
        "             \\  \\__/  /                ",
        "              '.___.'                  ",
        "            ___/|__|\\___               ",
        "         __/   /|MARK|\\   \\__          ",
        "      O==\\____/ |____| \\____/==O       ",
        "              \\ |____| /               ",
        "              /|____|\\                 ",
        "             / /    \\ \\                ",
        "            /_/      \\_\\               ",
        "           /  /      \\  \\              ",
        "          /__/        \\__\\             ",
        "         /___\\        /___\\            ",
        "                                         ",
    )
)

BASE_BLOCK = _pad(
    (
        "              .------.              ",
        "             /  FACE  \\             ",
        "            |    __    |            ",
        "             \\  \\__/  /             ",
        "              '.___.'               ",
        "            ___/|__|\\___            ",
        "         __/  __|MARK|__  \\__       ",
        "        O====/  |____|  \\====O      ",
        "             \\  |____|  /           ",
        "              \\/|____|\\/            ",
        "              / /    \\ \\            ",
        "             /_/      \\_\\           ",
        "            /  /      \\  \\          ",
        "           /__/        \\__\\         ",
        "          /___\\        /___\\        ",
        "                                      ",
    )
)

BASE_SPECIAL = _pad(
    (
        "              .------.                    ",
        "             /  FACE  \\              *    ",
        "            |    __    |        *         ",
        "             \\  \\__/  /                   ",
        "              '.___.'            *        ",
        "            ___/|__|\\________________@    ",
        "         __/   /|MARK|\\          ***      ",
        "        /  ___/ |____| \\                  ",
        "       O  /     |____|                    ",
        "          |    /|____|\\                   ",
        "          O   / /    \\ \\                  ",
        "             /_/      \\_\\                 ",
        "            /  /      \\  \\                ",
        "           /__/        \\__\\               ",
        "          /___\\        /___\\              ",
        "                                            ",
    )
)

BASE_FINISHER = _pad(
    (
        "       *      .------.      *       ",
        "             /  FACE  \\             ",
        "       O====|    __    |====O       ",
        "             \\  \\__/  /             ",
        "        *     '.___.'      *        ",
        "            ___/|__|\\___            ",
        "         __/   /|MARK|\\   \\__       ",
        "        /  ___/ |____| \\___  \\      ",
        "       O  /     |____|     \\  O     ",
        "             __/|____|\\__           ",
        "            /  /    \\  \\            ",
        "           /__/      \\__\\           ",
        "          /___\\      /___\\          ",
        "                                      ",
        "              FINISH                  ",
        "                                      ",
    )
)

BASE_HIT = _pad(
    (
        "              .------.   *          ",
        "             /  x  x  \\             ",
        "            |    __    |            ",
        "             \\   --   /             ",
        "              '.___.'               ",
        "             __/|__|\\__             ",
        "          __/  /|MARK|\\  \\__        ",
        "         O  __/ |____| \\__  O       ",
        "           /    |____|    \\         ",
        "          /    /|____|\\    \\        ",
        "         O    / /    \\ \\    O       ",
        "             /_/      \\_\\           ",
        "            /  /      \\  \\          ",
        "           /__/        \\__\\         ",
        "          /___\\        /___\\        ",
        "                                      ",
    )
)

BASE_KO = _pad(
    (
        "                                      ",
        "                                      ",
        "                                      ",
        "                                      ",
        "                                      ",
        "                                      ",
        "       .------.____                  ",
        "      /  x  x  \\   \\____             ",
        "     |    __    |       \\___         ",
        "      \\___--___/  MARK     \\==O      ",
        "       O==|____|____/\\_____/         ",
        "          /___\\      /___\\           ",
        "                                      ",
        "                                      ",
        "                                      ",
        "                                      ",
    )
)

BASE_VICTORY = _pad(
    (
        "        O\\      .------.      /O     ",
        "          \\    /  FACE  \\    /       ",
        "           \\  |    __    |  /        ",
        "            \\  \\  \\__/  /  /         ",
        "             \\__'.___.'__/          ",
        "                /|__|\\              ",
        "               /|MARK|\\             ",
        "              / |____| \\            ",
        "             /  |____|  \\           ",
        "            O  /|____|\\  O          ",
        "              / /    \\ \\            ",
        "             /_/      \\_\\           ",
        "            /__/      \\__\\          ",
        "           /___\\      /___\\         ",
        "              VICTORY                 ",
        "                                      ",
    )
)


def _animation_set(face: str, mark: str) -> dict[Action, tuple[str, ...]]:
    replacements = {"FACE": face, "MARK": mark}
    return {
        "idle": _hero_scale(_variant(BASE_IDLE, replacements)),
        "walk": _hero_scale(_variant(BASE_WALK, replacements)),
        "crouch": _hero_scale(_variant(BASE_CROUCH, replacements)),
        "jump": _hero_scale(_variant(BASE_JUMP, replacements)),
        "punch": _hero_scale(_variant(BASE_PUNCH, replacements)),
        "kick": _hero_scale(_variant(BASE_KICK, replacements)),
        "low_kick": _hero_scale(_variant(BASE_LOW_KICK, replacements)),
        "heavy": _hero_scale(_variant(BASE_HEAVY, replacements)),
        "sweep": _hero_scale(_variant(BASE_SWEEP, replacements)),
        "throw": _hero_scale(_variant(BASE_THROW, replacements)),
        "block": _hero_scale(_variant(BASE_BLOCK, replacements)),
        "special": _hero_scale(_variant(BASE_SPECIAL, replacements)),
        "finisher": _hero_scale(_variant(BASE_FINISHER, replacements)),
        "hit": _hero_scale(_variant(BASE_HIT, replacements)),
        "ko": _hero_scale(_variant(BASE_KO, replacements)),
        "victory": _hero_scale(_variant(BASE_VICTORY, replacements)),
    }


def build_roster() -> tuple[FighterSpec, ...]:
    """Return the original large-sprite fighter roster."""
    return (
        FighterSpec(
            id="volt",
            name="Volt",
            style="Balanced storm striker",
            max_health=128,
            speed=3,
            reach_bonus=0,
            special_name="Arc Pulse",
            finisher_name="Thunder Sever",
            palette=2,
            animations=_animation_set("o  o", "VOLT"),
        ),
        FighterSpec(
            id="nyx",
            name="Nyx",
            style="Fast shadow assassin",
            max_health=112,
            speed=4,
            reach_bonus=-1,
            special_name="Vanish Cut",
            finisher_name="Nightfall Split",
            palette=6,
            animations=_animation_set("^  ^", "NYX "),
        ),
        FighterSpec(
            id="kade",
            name="Kade",
            style="Heavy iron brawler",
            max_health=148,
            speed=2,
            reach_bonus=2,
            special_name="Iron Breaker",
            finisher_name="Anvil Drop",
            palette=1,
            animations=_animation_set("0  0", "KADE"),
        ),
    )


def new_fighter(spec: FighterSpec, x: int, facing: int, wins: int = 0) -> FighterState:
    return FighterState(spec=spec, x=x, facing=facing, health=spec.max_health, wins=wins)


def new_match(
    player_index: int = 0,
    enemy_index: int | None = None,
    arena_width: int = ARENA_WIDTH,
) -> CombatState:
    roster = build_roster()
    player_spec = roster[player_index % len(roster)]
    if enemy_index is None:
        enemy_index = (player_index + 1) % len(roster)
    enemy_spec = roster[enemy_index % len(roster)]
    player = new_fighter(player_spec, arena_width // 4, 1)
    enemy = new_fighter(enemy_spec, (arena_width * 3) // 4, -1)
    return CombatState(roster=roster, player=player, enemy=enemy, arena_width=arena_width, effects=[])


def select_fighter(index: int, delta: int, roster: tuple[FighterSpec, ...] | None = None) -> int:
    roster = roster or build_roster()
    if not roster:
        return 0
    return (index + delta) % len(roster)


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def sprite_width(sprite: tuple[str, ...]) -> int:
    return max(len(line) for line in sprite)


def sprite_height(sprite: tuple[str, ...]) -> int:
    return len(sprite)


def mirror_sprite(sprite: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(line.translate(MIRROR_TABLE)[::-1] for line in sprite)


def fighter_distance(state: CombatState) -> int:
    return abs(state.enemy.x - state.player.x)


def update_facing(state: CombatState) -> None:
    if state.player.x <= state.enemy.x:
        state.player.facing = 1
        state.enemy.facing = -1
    else:
        state.player.facing = -1
        state.enemy.facing = 1


def can_control(fighter: FighterState) -> bool:
    return (
        fighter.health > 0
        and fighter.hit_stun <= 0
        and fighter.action_timer <= 0
        and fighter.block_timer <= 0
        and fighter.cooldown <= 0
    )


def _side_pair(state: CombatState, side: Side) -> tuple[FighterState, FighterState]:
    if side == "player":
        return state.player, state.enemy
    return state.enemy, state.player


def move_fighter(state: CombatState, side: Side, direction: int) -> bool:
    fighter, opponent = _side_pair(state, side)
    if state.phase != "playing" or not can_control(fighter):
        return False

    target = clamp(fighter.x + direction * fighter.spec.speed, 10, state.arena_width - 10)
    if fighter.x <= opponent.x:
        target = min(target, opponent.x - MIN_FIGHTER_GAP)
    else:
        target = max(target, opponent.x + MIN_FIGHTER_GAP)
    target = clamp(target, 10, state.arena_width - 10)
    if target == fighter.x:
        return False

    fighter.x = target
    fighter.action = "walk"
    update_facing(state)
    return True


def start_crouch(state: CombatState, side: Side) -> bool:
    fighter, _ = _side_pair(state, side)
    if state.phase != "playing" or not can_control(fighter):
        return False
    fighter.action = "crouch"
    fighter.action_timer = 8
    fighter.cooldown = 2
    return True


def start_jump(state: CombatState, side: Side) -> bool:
    fighter, _ = _side_pair(state, side)
    if state.phase != "playing" or not can_control(fighter):
        return False
    fighter.action = "jump"
    fighter.action_timer = JUMP_FRAMES
    fighter.cooldown = 3
    return True


def start_block(state: CombatState, side: Side) -> bool:
    fighter, _ = _side_pair(state, side)
    if state.phase != "playing" or not can_control(fighter):
        return False
    fighter.action = "block"
    fighter.block_timer = 12
    fighter.cooldown = 3
    fighter.meter = min(METER_MAX, fighter.meter + 2)
    return True


def can_use_finisher(attacker: FighterState, defender: FighterState) -> bool:
    return defender.health <= FINISHER_HEALTH and attacker.meter >= ATTACKS["finisher"].meter_cost


def start_attack(state: CombatState, side: Side, attack: AttackName) -> bool:
    attacker, defender = _side_pair(state, side)
    if state.phase != "playing" or not can_control(attacker):
        return False

    spec = ATTACKS[attack]
    if spec.requires_finisher_window and not can_use_finisher(attacker, defender):
        state.message = (
            f"{attacker.spec.name} needs the foe at {FINISHER_HEALTH} HP or less "
            f"and {spec.meter_cost} meter."
        )
        state.message_timer = FPS
        return False
    if attacker.meter < spec.meter_cost:
        state.message = f"{attacker.spec.name} needs more meter for {attacker.spec.special_name}."
        state.message_timer = FPS
        return False

    attacker.meter -= spec.meter_cost
    attacker.action = spec.action
    attacker.action_timer = spec.frames
    attacker.cooldown = spec.cooldown

    reach = spec.reach + attacker.spec.reach_bonus
    if fighter_distance(state) <= reach:
        _deal_damage(state, side, spec)
    else:
        state.message = f"{attacker.spec.name} whiffs {spec.label}."
        state.message_timer = FPS
        _add_effect(state, "whiff", attacker.x + attacker.facing * reach, 0)
    return True


def _deal_damage(state: CombatState, attacker_side: Side, attack: AttackSpec) -> None:
    attacker, defender = _side_pair(state, attacker_side)
    blocked = defender.block_timer > 0 and defender.health > 0 and not attack.unblockable
    damage = attack.damage
    if blocked:
        damage = max(1, damage // 3)
        defender.meter = min(METER_MAX, defender.meter + 9)
        attacker.meter = min(METER_MAX, attacker.meter + 3)
        state.message = f"{defender.spec.name} blocks {attack.label}!"
        _add_effect(state, "block", defender.x, 0)
    else:
        defender.hit_stun = attack.stun
        defender.action = "hit"
        attacker.meter = min(METER_MAX, attacker.meter + attack.meter_gain)
        attacker.combo = attacker.combo + 1 if attacker.combo_timer > 0 else 1
        attacker.combo_timer = COMBO_WINDOW_FRAMES
        if attacker_side == "player":
            state.player_score += damage + max(0, attacker.combo - 1) * 6
        if attack.action == "special":
            state.message = f"{attacker.spec.name} lands {attacker.spec.special_name}!"
        elif attack.action == "finisher":
            state.message = f"{attacker.spec.name} unleashes {attacker.spec.finisher_name}!"
        else:
            state.message = f"{attacker.spec.name} lands {attack.label}!"
        _add_effect(state, "hit", defender.x, 0)

    defender.health = max(0, defender.health - damage)
    _apply_knockback(state, defender, attacker.facing, attack.knockback)
    state.message_timer = FPS
    _check_round_end(state)


def _apply_knockback(state: CombatState, defender: FighterState, direction: int, distance: int) -> None:
    defender.x = clamp(defender.x + direction * distance, 10, state.arena_width - 10)
    if state.player.x <= state.enemy.x:
        state.player.x = min(state.player.x, state.enemy.x - MIN_FIGHTER_GAP)
    else:
        state.player.x = max(state.player.x, state.enemy.x + MIN_FIGHTER_GAP)
    update_facing(state)


def _add_effect(state: CombatState, kind: str, x: int, y: int) -> None:
    if state.effects is None:
        state.effects = []
    state.effects.append(VisualEffect(kind=kind, x=x, y=y))
    state.effects = state.effects[-12:]


def tick_fighter(fighter: FighterState) -> None:
    if fighter.cooldown > 0:
        fighter.cooldown -= 1
    if fighter.action_timer > 0:
        fighter.action_timer -= 1
    if fighter.hit_stun > 0:
        fighter.hit_stun -= 1
    if fighter.block_timer > 0:
        fighter.block_timer -= 1
    if fighter.combo_timer > 0:
        fighter.combo_timer -= 1
    else:
        fighter.combo = 0

    if fighter.action == "jump":
        progress = JUMP_FRAMES - fighter.action_timer
        fighter.y_offset = max(0, int(7 * math.sin(math.pi * progress / JUMP_FRAMES)))
    else:
        fighter.y_offset = 0

    if fighter.health <= 0:
        fighter.action = "ko"
        fighter.y_offset = 0
    elif fighter.hit_stun > 0:
        fighter.action = "hit"
    elif fighter.block_timer > 0:
        fighter.action = "block"
    elif fighter.action_timer > 0:
        pass
    else:
        fighter.action = "idle"


def _tick_effects(state: CombatState) -> None:
    if state.effects is None:
        state.effects = []
    next_effects = []
    for effect in state.effects:
        effect.age += 1
        if effect.age < effect.duration:
            next_effects.append(effect)
    state.effects = next_effects


def choose_cpu_action(state: CombatState, rng: random.Random | None = None) -> str:
    rng = rng or random
    enemy = state.enemy
    player = state.player
    if state.phase != "playing" or not can_control(enemy):
        return "idle"

    distance = fighter_distance(state)
    if can_use_finisher(enemy, player) and rng.random() < 0.36:
        return "finisher"
    if player.action in {"punch", "kick", "heavy", "special"} and distance <= 18 and rng.random() < 0.42:
        return "block"
    if distance > 34:
        return "advance"
    if distance > 22 and rng.random() < 0.28:
        return "jump"
    if distance < 7 and rng.random() < 0.25:
        return "retreat"
    if enemy.health < enemy.spec.max_health * 0.35 and rng.random() < 0.18:
        return "block"
    if enemy.meter >= ATTACKS["special"].meter_cost and distance <= 24 and rng.random() < 0.24:
        return "special"
    best_basic_reach = max(spec.reach for spec in ATTACKS.values() if spec.meter_cost == 0)
    if distance > best_basic_reach + enemy.spec.reach_bonus:
        return "advance"
    roll = rng.random()
    if distance <= 7 and roll < 0.18:
        return "throw"
    if roll < 0.30:
        return "low_kick"
    if roll < 0.54:
        return "kick"
    if roll < 0.72:
        return "heavy"
    if roll < 0.88:
        return "sweep"
    return "punch"


def apply_cpu_action(state: CombatState, action: str) -> bool:
    if action == "advance":
        direction = -1 if state.enemy.x > state.player.x else 1
        return move_fighter(state, "enemy", direction)
    if action == "retreat":
        direction = 1 if state.enemy.x > state.player.x else -1
        return move_fighter(state, "enemy", direction)
    if action == "jump":
        return start_jump(state, "enemy")
    if action == "crouch":
        return start_crouch(state, "enemy")
    if action == "block":
        return start_block(state, "enemy")
    if action in ATTACKS:
        return start_attack(state, "enemy", action)  # type: ignore[arg-type]
    return False


def update_state(state: CombatState, rng: random.Random | None = None) -> None:
    if state.phase != "playing":
        return

    apply_cpu_action(state, choose_cpu_action(state, rng))
    tick_fighter(state.player)
    tick_fighter(state.enemy)
    _tick_effects(state)
    if state.message_timer > 0:
        state.message_timer -= 1
    state.round_frames_left = max(0, state.round_frames_left - 1)
    _check_round_end(state)


def _advance_fixed_timestep(
    state: CombatState,
    rng: random.Random,
    last_tick: float,
    now: float,
) -> float:
    catch_up_steps = 0
    while now - last_tick >= FRAME_TIME and catch_up_steps < MAX_CATCH_UP_STEPS:
        update_state(state, rng)
        last_tick += FRAME_TIME
        catch_up_steps += 1
    if now - last_tick >= FRAME_TIME:
        return now
    return last_tick


def _check_round_end(state: CombatState) -> None:
    if state.phase != "playing":
        return

    winner: Side | None = None
    if state.player.health <= 0 and state.enemy.health <= 0:
        winner = None
    elif state.enemy.health <= 0:
        winner = "player"
    elif state.player.health <= 0:
        winner = "enemy"
    elif state.round_frames_left <= 0:
        if state.player.health > state.enemy.health:
            winner = "player"
        elif state.enemy.health > state.player.health:
            winner = "enemy"

    if state.round_frames_left > 0 and winner is None and state.player.health > 0 and state.enemy.health > 0:
        return

    state.last_winner = winner
    if winner == "player":
        state.player.wins += 1
        state.player_score += 125 + state.player.health
        state.message = f"{state.player.spec.name} wins round {state.round_number}!"
    elif winner == "enemy":
        state.enemy.wins += 1
        state.message = f"{state.enemy.spec.name} wins round {state.round_number}!"
    else:
        state.message = f"Round {state.round_number} is a draw."

    if state.player.wins >= ROUNDS_TO_WIN:
        state.phase = "match_over"
        state.match_winner = "player"
        state.player.action = "victory"
        state.enemy.action = "ko"
        state.message = f"{state.player.spec.name} wins the match."
    elif state.enemy.wins >= ROUNDS_TO_WIN:
        state.phase = "match_over"
        state.match_winner = "enemy"
        state.enemy.action = "victory"
        state.player.action = "ko"
        state.message = f"{state.enemy.spec.name} wins the match."
    else:
        state.phase = "round_over"
    state.message_timer = FPS * 4


def start_next_round(state: CombatState) -> bool:
    if state.phase != "round_over":
        return False
    state.round_number += 1
    player_wins = state.player.wins
    enemy_wins = state.enemy.wins
    player_meter = state.player.meter
    enemy_meter = state.enemy.meter
    state.player = new_fighter(state.player.spec, state.arena_width // 4, 1, wins=player_wins)
    state.enemy = new_fighter(state.enemy.spec, (state.arena_width * 3) // 4, -1, wins=enemy_wins)
    state.player.meter = min(METER_MAX, player_meter + 12)
    state.enemy.meter = min(METER_MAX, enemy_meter + 12)
    state.round_frames_left = ROUND_FRAMES
    state.phase = "playing"
    state.last_winner = None
    state.effects = []
    state.message = f"Round {state.round_number} - FIGHT!"
    state.message_timer = FPS * 2
    return True


def restart_match(state: CombatState) -> CombatState:
    player_index = next(index for index, spec in enumerate(state.roster) if spec.id == state.player.spec.id)
    enemy_index = next(index for index, spec in enumerate(state.roster) if spec.id == state.enemy.spec.id)
    return new_match(player_index, enemy_index, state.arena_width)


def toggle_pause(state: CombatState) -> None:
    if state.phase == "playing":
        state.phase = "paused"
        state.message = "Paused"
    elif state.phase == "paused":
        state.phase = "playing"
        state.message = "FIGHT!"
    state.message_timer = FPS


def init_colors() -> bool:
    if not curses.has_colors():
        return False
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_CYAN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_GREEN, -1)
    curses.init_pair(5, curses.COLOR_WHITE, -1)
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)
    return True


def _bar(current: int, maximum: int, width: int, fill: str = "█") -> str:
    maximum = max(1, maximum)
    filled = clamp(int((current / maximum) * width), 0, width)
    return fill * filled + "░" * (width - filled)


def _draw_small_terminal(stdscr, height: int, width: int) -> None:
    stdscr.erase()
    msg = f"Terminal too small ({width}x{height}). Need {MIN_WIDTH}x{MIN_HEIGHT}."
    hint = "Resize for large fighters, or press Q/Esc to quit."
    safe_addstr(stdscr, height // 2 - 1, max(0, (width - len(msg)) // 2), msg, curses.A_BOLD)
    safe_addstr(stdscr, height // 2 + 1, max(0, (width - len(hint)) // 2), hint, curses.A_DIM)
    stdscr.refresh()


def render_title(stdscr, selected: int, roster: tuple[FighterSpec, ...], has_color: bool) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    if height < MIN_HEIGHT or width < MIN_WIDTH:
        _draw_small_terminal(stdscr, height, width)
        return

    title_attr = curses.color_pair(3) | curses.A_BOLD if has_color else curses.A_BOLD
    accent_attr = curses.color_pair(2) | curses.A_BOLD if has_color else curses.A_BOLD
    dim_attr = curses.A_DIM

    y = 1
    for line in TITLE_ART:
        safe_addstr(stdscr, y, max(0, (width - len(line)) // 2), line, title_attr)
        y += 1

    subtitle = "Large-sprite 16-bit terminal fighter. Choose a warrior. Best of three."
    safe_addstr(stdscr, y + 1, max(0, (width - len(subtitle)) // 2), subtitle, accent_attr)

    card_w = 32
    gap = 3
    total_w = len(roster) * card_w + (len(roster) - 1) * gap
    start_x = max(2, (width - total_w) // 2)
    card_y = y + 4
    for index, spec in enumerate(roster):
        x = start_x + index * (card_w + gap)
        selected_card = index == selected
        attr = (curses.A_REVERSE | curses.A_BOLD) if selected_card else curses.A_BOLD
        safe_addstr(stdscr, card_y, x, "╔" + "═" * (card_w - 2) + "╗", attr)
        safe_addstr(stdscr, card_y + 1, x, "║" + spec.name.center(card_w - 2) + "║", attr)
        safe_addstr(stdscr, card_y + 2, x, "║" + spec.style[: card_w - 2].center(card_w - 2) + "║", attr)
        safe_addstr(stdscr, card_y + 3, x, "║" + f"HP {spec.max_health}  SPD {spec.speed}".center(card_w - 2) + "║", attr)
        safe_addstr(stdscr, card_y + 4, x, "║" + f"Special: {spec.special_name}"[: card_w - 2].center(card_w - 2) + "║", attr)
        safe_addstr(stdscr, card_y + 5, x, "║" + f"Finisher: {spec.finisher_name}"[: card_w - 2].center(card_w - 2) + "║", attr)
        safe_addstr(stdscr, card_y + 6, x, "╚" + "═" * (card_w - 2) + "╝", attr)

    controls = "Left/Right or A/D choose   Enter/Space fight   Q quit"
    safe_addstr(stdscr, height - 3, max(0, (width - len(controls)) // 2), controls, dim_attr)
    stdscr.refresh()


def _sprite_for(fighter: FighterState) -> tuple[str, ...]:
    action = fighter.action
    if fighter.health <= 0:
        action = "ko"
    sprite = fighter.spec.animations.get(action, fighter.spec.animations["idle"])
    return sprite if fighter.facing >= 0 else mirror_sprite(sprite)


def _attr_for_fighter(fighter: FighterState, has_color: bool) -> int:
    if not has_color:
        return curses.A_BOLD
    return curses.color_pair(fighter.spec.palette) | curses.A_BOLD


def _draw_stage(stdscr, arena_x: int, floor_y: int, arena_width: int, has_color: bool) -> None:
    dim = curses.color_pair(5) if has_color else curses.A_DIM
    accent = curses.color_pair(3) | curses.A_BOLD if has_color else curses.A_BOLD
    safe_addstr(stdscr, floor_y - 20, arena_x, "╔" + "═" * arena_width + "╗", dim)
    for row in range(1, 20):
        motif = "░" * arena_width
        if row in {5, 11, 17}:
            motif = ("▁▂▃▄▅▆▇" * ((arena_width // 7) + 1))[:arena_width]
        safe_addstr(stdscr, floor_y - 20 + row, arena_x, "║" + motif + "║", dim)
    safe_addstr(stdscr, floor_y - 4, arena_x + 3, "▌▌  SHADOW CIRCUIT ARENA  ▐▐", accent)
    safe_addstr(stdscr, floor_y, arena_x, "╠" + "═" * arena_width + "╣", dim)
    safe_addstr(stdscr, floor_y + 1, arena_x, "║" + "▓" * arena_width + "║", dim)
    safe_addstr(stdscr, floor_y + 2, arena_x, "╚" + "═" * arena_width + "╝", dim)


def _draw_effects(stdscr, state: CombatState, arena_x: int, floor_y: int, has_color: bool) -> None:
    attr = curses.color_pair(3) | curses.A_BOLD if has_color else curses.A_BOLD
    for effect in state.effects or []:
        if effect.kind == "block":
            frames = ("<██>", "<▒▒>", "<░░>")
        elif effect.kind == "whiff":
            frames = ("~~~", "···", "   ")
        else:
            frames = ("✦██✦", " ✷✷ ", "  ✦ ")
        frame = frames[min(len(frames) - 1, effect.age // 3)]
        safe_addstr(stdscr, floor_y - 11 + effect.y, arena_x + effect.x, frame, attr)


def render_game(stdscr, state: CombatState, has_color: bool) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    if height < MIN_HEIGHT or width < MIN_WIDTH:
        _draw_small_terminal(stdscr, height, width)
        return

    red = curses.color_pair(1) | curses.A_BOLD if has_color else curses.A_BOLD
    cyan = curses.color_pair(2) | curses.A_BOLD if has_color else curses.A_BOLD
    yellow = curses.color_pair(3) | curses.A_BOLD if has_color else curses.A_BOLD
    green = curses.color_pair(4) | curses.A_BOLD if has_color else curses.A_BOLD
    magenta = curses.color_pair(6) | curses.A_BOLD if has_color else curses.A_BOLD

    player_name = f"{state.player.spec.name}  {'●' * state.player.wins}"
    enemy_name = f"{'●' * state.enemy.wins}  {state.enemy.spec.name}"
    timer = max(0, state.round_frames_left // FPS)
    safe_addstr(stdscr, 1, 3, player_name, cyan)
    safe_addstr(stdscr, 1, width - len(enemy_name) - 3, enemy_name, red)
    safe_addstr(stdscr, 1, max(0, (width - 14) // 2), f"ROUND {state.round_number}  {timer:02}", yellow)

    bar_w = 42
    safe_addstr(stdscr, 3, 3, "LIFE [" + _bar(state.player.health, state.player.spec.max_health, bar_w) + "]", green)
    enemy_bar = "LIFE [" + _bar(state.enemy.health, state.enemy.spec.max_health, bar_w) + "]"
    safe_addstr(stdscr, 3, width - len(enemy_bar) - 3, enemy_bar, green)
    safe_addstr(stdscr, 4, 3, "METER[" + _bar(state.player.meter, METER_MAX, 24, "■") + "]", cyan)
    enemy_meter = "METER[" + _bar(state.enemy.meter, METER_MAX, 24, "■") + "]"
    safe_addstr(stdscr, 4, width - len(enemy_meter) - 3, enemy_meter, red)

    arena_x = max(2, (width - state.arena_width - 2) // 2)
    floor_y = height - 6
    _draw_stage(stdscr, arena_x, floor_y, state.arena_width, has_color)
    _draw_effects(stdscr, state, arena_x, floor_y, has_color)

    for fighter in (state.player, state.enemy):
        sprite = _sprite_for(fighter)
        sprite_x = arena_x + fighter.x - sprite_width(sprite) // 2
        sprite_y = floor_y - sprite_height(sprite) - fighter.y_offset
        attr = _attr_for_fighter(fighter, has_color)
        for row, line in enumerate(sprite):
            safe_addstr(stdscr, sprite_y + row, sprite_x, line, attr)
        label = f"{fighter.spec.name} [{fighter.action}]"
        safe_addstr(stdscr, floor_y + 3, sprite_x, label[: max(1, sprite_width(sprite))], attr)

    if state.message_timer > 0 or state.phase != "playing":
        attr = magenta if state.phase in {"round_over", "match_over"} else yellow
        safe_addstr(stdscr, 7, max(0, (width - len(state.message)) // 2), state.message, attr)

    if state.phase == "paused":
        pause_msg = "PAUSED"
        safe_addstr(stdscr, height // 2, max(0, (width - len(pause_msg)) // 2), pause_msg, curses.A_REVERSE | curses.A_BOLD)
    elif state.phase == "round_over":
        msg = "Enter/Space next round   R restart   Q quit"
        safe_addstr(stdscr, height - 4, max(0, (width - len(msg)) // 2), msg, yellow)
    elif state.phase == "match_over":
        msg = "R rematch   Q quit"
        safe_addstr(stdscr, height - 4, max(0, (width - len(msg)) // 2), msg, yellow)

    controls = "A/D move  W jump  S crouch  J punch  K kick  U low  O heavy  H sweep  ; throw  L block  I special  F finisher"
    safe_addstr(stdscr, height - 2, max(0, (width - len(controls)) // 2), controls, curses.A_DIM)
    stdscr.refresh()


def _handle_play_key(state: CombatState, key: int) -> CombatState:
    if key in QUIT_KEYS:
        state.running = False
    elif key in PAUSE_KEYS:
        toggle_pause(state)
    elif key in RESTART_KEYS:
        state = restart_match(state)
    elif state.phase == "round_over" and key in CONFIRM_KEYS:
        start_next_round(state)
    elif state.phase == "playing":
        if key in MOVE_LEFT_KEYS:
            move_fighter(state, "player", -1)
        elif key in MOVE_RIGHT_KEYS:
            move_fighter(state, "player", 1)
        elif key in JUMP_KEYS:
            start_jump(state, "player")
        elif key in CROUCH_KEYS:
            start_crouch(state, "player")
        elif key in PUNCH_KEYS:
            start_attack(state, "player", "punch")
        elif key in KICK_KEYS:
            start_attack(state, "player", "kick")
        elif key in LOW_KICK_KEYS:
            start_attack(state, "player", "low_kick")
        elif key in HEAVY_KEYS:
            start_attack(state, "player", "heavy")
        elif key in SWEEP_KEYS:
            start_attack(state, "player", "sweep")
        elif key in THROW_KEYS:
            start_attack(state, "player", "throw")
        elif key in BLOCK_KEYS:
            start_block(state, "player")
        elif key in SPECIAL_KEYS:
            start_attack(state, "player", "special")
        elif key in FINISHER_KEYS:
            start_attack(state, "player", "finisher")
    return state


def main(stdscr) -> None:
    hide_cursor()
    stdscr.keypad(True)
    stdscr.timeout(20)
    has_color = init_colors()
    roster = build_roster()
    selected = 0
    state: CombatState | None = None
    rng = random.Random()
    last_tick = time.monotonic()

    while True:
        height, width = stdscr.getmaxyx()
        key = stdscr.getch()

        if state is None:
            if key in QUIT_KEYS:
                return
            if height >= MIN_HEIGHT and width >= MIN_WIDTH:
                if key in MOVE_LEFT_KEYS:
                    selected = select_fighter(selected, -1, roster)
                elif key in MOVE_RIGHT_KEYS:
                    selected = select_fighter(selected, 1, roster)
                elif key in CONFIRM_KEYS or (ord("1") <= key <= ord("3")):
                    if ord("1") <= key <= ord("3"):
                        selected = key - ord("1")
                    state = new_match(selected)
                    last_tick = time.monotonic()
            render_title(stdscr, selected, roster, has_color)
            time.sleep(0.01)
            continue

        if key != -1:
            state = _handle_play_key(state, key)
            if not state.running:
                return

        now = time.monotonic()
        last_tick = _advance_fixed_timestep(state, rng, last_tick, now)

        render_game(stdscr, state, has_color)
        time.sleep(0.005)


def run() -> None:
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        return
