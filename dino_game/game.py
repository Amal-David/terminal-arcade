from __future__ import annotations

import curses
import random
import time
from dataclasses import dataclass, field

from .assets import (
    BIOME_BACKDROP_TILES,
    BIOME_GROUNDS,
    BIOME_LABELS,
    BIOME_SKYLINES,
    DEFAULT_DINOSAUR_KEY,
    DINOSAUR_BLURBS,
    DINOSAUR_BY_KEY,
    DINOSAUR_FRAMES,
    DINOSAUR_NAMES,
    DINOSAUR_ORDER,
    DINOSAUR_SHORT_NAMES,
    HAZARD_SPRITES,
    SCAVENGER_FRAMES,
)
from .audio import AudioManager
from .storage import load_high_score, save_high_score


FPS = 20
FRAME_TIME = 1.0 / FPS

INITIAL_SPEED = 1.7
MAX_SPEED = 4.8
SPEED_STEP = 0.22
SPEED_DRIFT_DIVISOR = 2200.0
SPEED_TIER_SCORE = 150

BASE_JUMP_VELOCITY = -5.25
GRAVITY = 0.72
FAST_FALL_MULTIPLIER = 2.3

CLEAR_TIME_FRAMES = 60
RESTART_DELAY_FRAMES = 12
MIN_WIDTH = 70
MIN_HEIGHT = 20
DINO_X = 10
SCORE_FLASH_FRAMES = 6
BIOME_LENGTH = 300
BANNER_FRAMES = 40

ROAR_CHARGE_MAX = 100.0
ROAR_CHARGE_PER_FRAME = 0.65
ROAR_TIMER_FRAMES = 10
ROAR_RANGE = 18
ROAR_SCORE_BONUS = 25

ACTION_NEUTRAL = "neutral"
ACTION_JUMP = "jump"
ACTION_DUCK = "duck"

JUMP_KEYS = {curses.KEY_UP, ord(" "), ord("w"), ord("W")}
DUCK_KEYS = {curses.KEY_DOWN, ord("s"), ord("S")}
ROAR_KEYS = {ord("x"), ord("X")}
RESTART_KEYS = {ord(" "), ord("r"), ord("R"), 10, 13}
QUIT_KEYS = {ord("q"), ord("Q"), 27}
PAUSE_KEYS = {ord("p"), ord("P")}
SELECT_LEFT_KEYS = {curses.KEY_LEFT, ord("a"), ord("A")}
SELECT_RIGHT_KEYS = {curses.KEY_RIGHT, ord("d"), ord("D")}
TITLE_NUMBER_KEYS = {
    ord("1"): 0,
    ord("2"): 1,
    ord("3"): 2,
    ord("4"): 3,
    ord("5"): 4,
    ord("6"): 5,
    ord("7"): 6,
    ord("8"): 7,
    ord("9"): 8,
    ord("0"): 9,
}

HERO_STANDING_BOX = (8, 6)
HERO_DUCK_BOX = (9, 3)
SCAVENGER_BOX = (5, 2)

TRANSITION_GAP_BONUS = {
    (ACTION_NEUTRAL, ACTION_NEUTRAL): 8,
    (ACTION_NEUTRAL, ACTION_JUMP): 11,
    (ACTION_NEUTRAL, ACTION_DUCK): 13,
    (ACTION_JUMP, ACTION_NEUTRAL): 10,
    (ACTION_JUMP, ACTION_JUMP): 13,
    (ACTION_JUMP, ACTION_DUCK): 20,
    (ACTION_DUCK, ACTION_NEUTRAL): 12,
    (ACTION_DUCK, ACTION_JUMP): 22,
    (ACTION_DUCK, ACTION_DUCK): 15,
}


@dataclass(frozen=True)
class HazardSpec:
    name: str
    sprite_key: str
    action: str
    fragile: bool
    biome: str
    min_speed: float = 0.0
    bird_y_offset: int = 0
    speed_offset: float = 0.0
    hitbox: tuple[int, int] = (5, 5)


@dataclass(frozen=True)
class PatternTemplate:
    name: str
    biome: str
    hazards: tuple[tuple[str, int], ...]
    min_speed: float
    action: str
    weight: int = 1

    @property
    def group_size(self) -> int:
        return len(self.hazards)


@dataclass
class Obstacle:
    x: float
    hazard_name: str
    biome: str

    @property
    def spec(self) -> HazardSpec:
        return HAZARD_SPECS[self.hazard_name]


@dataclass
class GameState:
    score: int = 0
    high_score: int = 0
    speed: float = INITIAL_SPEED
    started: bool = False
    is_dead: bool = False
    is_paused: bool = False
    frame_count: int = 0
    running_frames: int = 0

    is_jumping: bool = False
    is_ducking: bool = False
    dino_y: float = 0.0
    dino_vy: float = 0.0
    fast_falling: bool = False
    duck_timer: int = 0

    obstacles: list[Obstacle] = field(default_factory=list)
    ground_offset: float = 0.0
    ground_rough: bool = False
    ground_segment_remaining: float = 0.0
    pattern_history: list[str] = field(default_factory=list)
    last_pattern_name: str | None = None
    queued_pattern_name: str | None = None
    queued_gap: int = 0

    current_biome: str = "scrub"
    banner_text: str = BIOME_LABELS["scrub"]
    banner_timer: int = BANNER_FRAMES

    score_flash_timer: int = 0
    death_anim_frame: int = 0
    restart_delay: int = 0
    high_score_dirty: bool = False
    new_high_score: bool = False

    roar_charge: float = 0.0
    roar_timer: int = 0
    roar_ready_pinged: bool = False
    selected_dino: str = DEFAULT_DINOSAUR_KEY


HAZARD_SPECS = {
    "desert_pad": HazardSpec(
        name="desert_pad",
        sprite_key="desert_pad",
        action=ACTION_JUMP,
        fragile=True,
        biome="scrub",
        min_speed=0.0,
        hitbox=(3, 4),
    ),
    "desert_tall": HazardSpec(
        name="desert_tall",
        sprite_key="desert_tall",
        action=ACTION_JUMP,
        fragile=False,
        biome="scrub",
        min_speed=1.9,
        hitbox=(5, 6),
    ),
    "desert_stump": HazardSpec(
        name="desert_stump",
        sprite_key="desert_stump",
        action=ACTION_JUMP,
        fragile=True,
        biome="scrub",
        min_speed=1.2,
        hitbox=(5, 3),
    ),
    "fossil_ribs": HazardSpec(
        name="fossil_ribs",
        sprite_key="fossil_ribs",
        action=ACTION_JUMP,
        fragile=False,
        biome="fossil",
        min_speed=2.2,
        hitbox=(7, 4),
    ),
    "fossil_spire": HazardSpec(
        name="fossil_spire",
        sprite_key="fossil_spire",
        action=ACTION_JUMP,
        fragile=False,
        biome="fossil",
        min_speed=2.4,
        hitbox=(5, 5),
    ),
    "fossil_heap": HazardSpec(
        name="fossil_heap",
        sprite_key="fossil_heap",
        action=ACTION_JUMP,
        fragile=True,
        biome="fossil",
        min_speed=2.2,
        hitbox=(6, 3),
    ),
    "basalt_spike": HazardSpec(
        name="basalt_spike",
        sprite_key="basalt_spike",
        action=ACTION_JUMP,
        fragile=False,
        biome="basalt",
        min_speed=2.9,
        hitbox=(5, 6),
    ),
    "basalt_vent": HazardSpec(
        name="basalt_vent",
        sprite_key="basalt_vent",
        action=ACTION_JUMP,
        fragile=False,
        biome="basalt",
        min_speed=3.0,
        hitbox=(5, 4),
    ),
    "basalt_shards": HazardSpec(
        name="basalt_shards",
        sprite_key="basalt_shards",
        action=ACTION_JUMP,
        fragile=True,
        biome="basalt",
        min_speed=3.0,
        hitbox=(6, 4),
    ),
    "scavenger_high": HazardSpec(
        name="scavenger_high",
        sprite_key="scavenger",
        action=ACTION_NEUTRAL,
        fragile=True,
        biome="scrub",
        min_speed=2.5,
        bird_y_offset=-7,
        speed_offset=0.2,
        hitbox=SCAVENGER_BOX,
    ),
    "scavenger_mid": HazardSpec(
        name="scavenger_mid",
        sprite_key="scavenger",
        action=ACTION_JUMP,
        fragile=True,
        biome="fossil",
        min_speed=3.0,
        bird_y_offset=-4,
        speed_offset=0.25,
        hitbox=SCAVENGER_BOX,
    ),
    "scavenger_low": HazardSpec(
        name="scavenger_low",
        sprite_key="scavenger",
        action=ACTION_DUCK,
        fragile=True,
        biome="basalt",
        min_speed=3.4,
        bird_y_offset=-1,
        speed_offset=0.3,
        hitbox=SCAVENGER_BOX,
    ),
}

PATTERN_TEMPLATES = (
    PatternTemplate("scrub_pad", "scrub", (("desert_pad", 0),), 0.0, ACTION_JUMP, 6),
    PatternTemplate("scrub_tall", "scrub", (("desert_tall", 0),), 1.9, ACTION_JUMP, 4),
    PatternTemplate("scrub_stump", "scrub", (("desert_stump", 0),), 1.2, ACTION_JUMP, 4),
    PatternTemplate(
        "scrub_pair",
        "scrub",
        (("desert_pad", 0), ("desert_stump", 8)),
        2.4,
        ACTION_JUMP,
        2,
    ),
    PatternTemplate("scrub_scavenger", "scrub", (("scavenger_high", 0),), 2.5, ACTION_NEUTRAL, 2),
    PatternTemplate("fossil_ribs", "fossil", (("fossil_ribs", 0),), 2.2, ACTION_JUMP, 5),
    PatternTemplate("fossil_spire", "fossil", (("fossil_spire", 0),), 2.4, ACTION_JUMP, 4),
    PatternTemplate("fossil_heap", "fossil", (("fossil_heap", 0),), 2.2, ACTION_JUMP, 4),
    PatternTemplate(
        "fossil_pair",
        "fossil",
        (("fossil_heap", 0), ("fossil_spire", 8)),
        3.0,
        ACTION_JUMP,
        2,
    ),
    PatternTemplate("fossil_scavenger", "fossil", (("scavenger_mid", 0),), 3.0, ACTION_JUMP, 2),
    PatternTemplate("basalt_spike", "basalt", (("basalt_spike", 0),), 2.9, ACTION_JUMP, 5),
    PatternTemplate("basalt_vent", "basalt", (("basalt_vent", 0),), 3.0, ACTION_JUMP, 4),
    PatternTemplate("basalt_shards", "basalt", (("basalt_shards", 0),), 3.0, ACTION_JUMP, 4),
    PatternTemplate(
        "basalt_pair",
        "basalt",
        (("basalt_shards", 0), ("basalt_spike", 9)),
        3.5,
        ACTION_JUMP,
        2,
    ),
    PatternTemplate("basalt_scavenger", "basalt", (("scavenger_low", 0),), 3.4, ACTION_DUCK, 2),
)

PATTERN_BY_NAME = {pattern.name: pattern for pattern in PATTERN_TEMPLATES}


def selected_dinosaur_key(state: GameState) -> str:
    return state.selected_dino if state.selected_dino in DINOSAUR_BY_KEY else DEFAULT_DINOSAUR_KEY


def hero_frames_for(state: GameState) -> dict[str, list[list[str]] | list[str]]:
    return DINOSAUR_FRAMES[selected_dinosaur_key(state)]


def choose_dinosaur(state: GameState, index: int) -> bool:
    if not DINOSAUR_ORDER:
        return False
    next_key = DINOSAUR_ORDER[index % len(DINOSAUR_ORDER)]
    if state.selected_dino == next_key:
        return False
    state.selected_dino = next_key
    return True


def cycle_dinosaur(state: GameState, step: int) -> bool:
    current_key = selected_dinosaur_key(state)
    current_index = DINOSAUR_ORDER.index(current_key)
    return choose_dinosaur(state, current_index + step)


def sprite_lines(sprite_key: str, frame_count: int = 0) -> list[str]:
    if sprite_key == "scavenger":
        return SCAVENGER_FRAMES[(frame_count // 5) % 2]
    return HAZARD_SPRITES[sprite_key]


def sprite_dimensions(lines: list[str]) -> tuple[int, int]:
    return max(len(line) for line in lines), len(lines)


def pattern_width(pattern: PatternTemplate) -> int:
    width = 0
    for hazard_name, offset in pattern.hazards:
        spec = HAZARD_SPECS[hazard_name]
        sprite = sprite_lines(spec.sprite_key)
        hazard_width = sprite_dimensions(sprite)[0]
        width = max(width, offset + hazard_width)
    return width


def biome_for_score(score: int) -> str:
    keys = ("scrub", "fossil", "basalt")
    return keys[(score // BIOME_LENGTH) % len(keys)]


def speed_target(score: int) -> float:
    tier_bonus = (score // SPEED_TIER_SCORE) * SPEED_STEP
    drift_bonus = min(0.75, score / SPEED_DRIFT_DIVISOR)
    return min(MAX_SPEED, INITIAL_SPEED + tier_bonus + drift_bonus)


def available_patterns(biome: str, speed: float) -> list[PatternTemplate]:
    return [
        pattern
        for pattern in PATTERN_TEMPLATES
        if pattern.biome == biome and speed >= pattern.min_speed
    ]


def choose_pattern(biome: str, speed: float, history: list[str], rng: random.Random) -> PatternTemplate:
    candidates = available_patterns(biome, speed)
    if not candidates:
        return next(pattern for pattern in PATTERN_TEMPLATES if pattern.biome == biome)

    if len(history) >= 2 and history[-1] == history[-2]:
        filtered = [pattern for pattern in candidates if pattern.name != history[-1]]
        if filtered:
            candidates = filtered

    if history:
        last_pattern = PATTERN_BY_NAME[history[-1]]
        if last_pattern.group_size > 1:
            filtered = [pattern for pattern in candidates if pattern.group_size == 1]
            if filtered:
                candidates = filtered
        if last_pattern.action == ACTION_DUCK:
            filtered = [pattern for pattern in candidates if pattern.action != ACTION_DUCK]
            if filtered:
                candidates = filtered

    return rng.choices(candidates, weights=[pattern.weight for pattern in candidates], k=1)[0]


def required_pattern_gap(previous: PatternTemplate | None, upcoming: PatternTemplate, speed: float) -> int:
    previous_action = previous.action if previous else ACTION_NEUTRAL
    recovery = TRANSITION_GAP_BONUS[(previous_action, upcoming.action)]
    base = round(speed * 4) + pattern_width(upcoming)
    group_bonus = max(0, upcoming.group_size - 1) * 4
    previous_group_bonus = 3 if previous and previous.group_size > 1 else 0
    return max(18, base + recovery + group_bonus + previous_group_bonus)


def centered_hitbox(
    draw_x: int, draw_y: int, sprite: list[str], box_size: tuple[int, int]
) -> tuple[int, int, int, int]:
    sprite_width, sprite_height = sprite_dimensions(sprite)
    box_width, box_height = box_size
    left = draw_x + max(0, (sprite_width - box_width) // 2)
    top = draw_y + max(0, sprite_height - box_height)
    return (left, top, left + box_width, top + box_height)


def boxes_overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def get_hero_sprite(state: GameState) -> list[str]:
    frames = hero_frames_for(state)
    if state.is_dead:
        return frames["hit"]
    if state.roar_timer > 0:
        roar_frames = frames["roar"]
        return roar_frames[state.roar_timer % len(roar_frames)]
    if state.is_jumping:
        if state.dino_vy < -0.8:
            return frames["jump_up"]
        if state.dino_vy > 0.8:
            return frames["fall"]
        return frames["apex"]
    if state.is_ducking:
        duck_frames = frames["duck"]
        return duck_frames[(state.frame_count // 4) % len(duck_frames)]
    if not state.started:
        idle_frames = frames["idle"]
        return idle_frames[(state.frame_count // 12) % len(idle_frames)]
    run_frames = frames["run"]
    return run_frames[(state.frame_count // 2) % len(run_frames)]


def get_title_preview_sprite(state: GameState) -> list[str]:
    frames = hero_frames_for(state)
    phase = (state.frame_count // 18) % 5
    if phase == 4:
        roar_frames = frames["roar"]
        return roar_frames[(state.frame_count // 2) % len(roar_frames)]
    run_frames = frames["run"]
    return run_frames[(state.frame_count // 2) % len(run_frames)]


def get_hero_hitbox(state: GameState, ground_y: int) -> tuple[int, int, int, int]:
    sprite = get_hero_sprite(state)
    draw_y = ground_y - len(sprite) + int(state.dino_y)
    box_size = HERO_DUCK_BOX if state.is_ducking and not state.is_jumping else HERO_STANDING_BOX
    return centered_hitbox(DINO_X, draw_y, sprite, box_size)


def get_obstacle_sprite(obstacle: Obstacle, frame_count: int) -> list[str]:
    return sprite_lines(obstacle.spec.sprite_key, frame_count)


def get_obstacle_hitbox(obstacle: Obstacle, frame_count: int, ground_y: int) -> tuple[int, int, int, int]:
    sprite = get_obstacle_sprite(obstacle, frame_count)
    draw_y = ground_y - len(sprite)
    if obstacle.spec.sprite_key == "scavenger":
        draw_y += obstacle.spec.bird_y_offset
    return centered_hitbox(int(obstacle.x), draw_y, sprite, obstacle.spec.hitbox)


def safe_addstr(stdscr, y: int, x: int, text: str, attr: int = 0) -> None:
    height, width = stdscr.getmaxyx()
    if y < 0 or y >= height or x >= width:
        return
    if x < 0:
        text = text[-x:]
        x = 0
    max_len = width - x - 1
    if max_len <= 0:
        return
    try:
        stdscr.addstr(y, x, text[:max_len], attr)
    except curses.error:
        pass


def draw_sprite(stdscr, sprite: list[str], y: int, x: int, attr: int = 0) -> None:
    for index, line in enumerate(sprite):
        start = None
        for char_index, char in enumerate(line):
            if char != " " and start is None:
                start = char_index
            if char == " " and start is not None:
                safe_addstr(stdscr, y + index, x + start, line[start:char_index], attr)
                start = None
        if start is not None:
            safe_addstr(stdscr, y + index, x + start, line[start:], attr)


def start_jump(state: GameState) -> None:
    state.is_jumping = True
    state.is_ducking = False
    state.duck_timer = 0
    state.fast_falling = False
    state.dino_vy = BASE_JUMP_VELOCITY - state.speed * 0.12


def trigger_roar(state: GameState, audio: AudioManager | None = None) -> bool:
    if state.roar_charge < ROAR_CHARGE_MAX or state.roar_timer > 0:
        return False
    state.roar_charge = 0.0
    state.roar_timer = ROAR_TIMER_FRAMES
    state.roar_ready_pinged = False
    if audio is not None:
        audio.play("roar")
    return True


def handle_input(stdscr, state: GameState, audio: AudioManager) -> str | None:
    keys: list[int] = []
    while True:
        key = stdscr.getch()
        if key == -1:
            break
        keys.append(key)

    if any(key in QUIT_KEYS for key in keys):
        return "quit"

    has_jump = any(key in JUMP_KEYS for key in keys)
    has_duck = any(key in DUCK_KEYS for key in keys)
    has_roar = any(key in ROAR_KEYS for key in keys)
    has_restart = any(key in RESTART_KEYS for key in keys)
    has_pause = any(key in PAUSE_KEYS for key in keys)

    if not state.started:
        changed = False
        for key in keys:
            if key in SELECT_LEFT_KEYS:
                changed = cycle_dinosaur(state, -1) or changed
            elif key in SELECT_RIGHT_KEYS:
                changed = cycle_dinosaur(state, 1) or changed
            elif key in TITLE_NUMBER_KEYS and TITLE_NUMBER_KEYS[key] < len(DINOSAUR_ORDER):
                changed = choose_dinosaur(state, TITLE_NUMBER_KEYS[key]) or changed
        if changed:
            audio.play("menu")
        if has_jump or has_restart:
            state.started = True
            audio.start_music()
            audio.play("menu")
        return None

    if has_pause and not state.is_dead:
        state.is_paused = not state.is_paused
        audio.play("pause")
        return None

    if state.is_paused:
        return None

    if state.is_dead:
        if state.restart_delay > 0:
            state.restart_delay -= 1
            return None
        if has_restart:
            audio.play("menu")
            return "restart"
        return None

    if has_roar:
        trigger_roar(state, audio)

    if has_jump and not state.is_jumping:
        start_jump(state)
        audio.play("jump")

    if has_duck:
        if state.is_jumping:
            state.fast_falling = True
            if state.dino_vy < 0:
                state.dino_vy = 1.0
        else:
            state.is_ducking = True
            state.duck_timer = 4
    else:
        if state.duck_timer > 0:
            state.duck_timer -= 1
        else:
            state.is_ducking = False

    return None


def update_physics(state: GameState, audio: AudioManager) -> None:
    if state.roar_timer > 0:
        state.roar_timer -= 1

    if not state.is_jumping:
        return

    gravity = GRAVITY * (FAST_FALL_MULTIPLIER if state.fast_falling else 1.0)
    state.dino_vy += gravity
    state.dino_y += state.dino_vy

    if state.dino_y >= 0:
        state.dino_y = 0
        state.dino_vy = 0
        state.is_jumping = False
        state.fast_falling = False
        audio.play("land")


def ensure_queued_pattern(state: GameState, rng: random.Random) -> None:
    if state.queued_pattern_name is not None:
        return
    biome = state.current_biome
    previous = PATTERN_BY_NAME[state.last_pattern_name] if state.last_pattern_name else None
    next_pattern = choose_pattern(biome, state.speed, state.pattern_history, rng)
    state.queued_pattern_name = next_pattern.name
    state.queued_gap = required_pattern_gap(previous, next_pattern, state.speed)


def spawn_queued_pattern(state: GameState, screen_width: int) -> None:
    if state.queued_pattern_name is None:
        return
    pattern = PATTERN_BY_NAME[state.queued_pattern_name]
    previous = PATTERN_BY_NAME[state.last_pattern_name] if state.last_pattern_name else None
    spawn_offset = pattern_width(previous) if previous else 6
    start_x = float(screen_width + spawn_offset)

    for hazard_name, offset in pattern.hazards:
        state.obstacles.append(Obstacle(x=start_x + offset, hazard_name=hazard_name, biome=pattern.biome))

    state.last_pattern_name = pattern.name
    state.pattern_history.append(pattern.name)
    if len(state.pattern_history) > 6:
        state.pattern_history.pop(0)
    state.queued_pattern_name = None
    state.queued_gap = 0


def update_obstacles(state: GameState, screen_width: int, rng: random.Random) -> None:
    for obstacle in state.obstacles:
        obstacle.x -= state.speed + obstacle.spec.speed_offset

    state.obstacles = [obstacle for obstacle in state.obstacles if obstacle.x > -24]

    if state.running_frames < CLEAR_TIME_FRAMES:
        return

    ensure_queued_pattern(state, rng)
    if not state.obstacles:
        spawn_queued_pattern(state, screen_width)
        return

    rightmost = max(
        obstacle.x + sprite_dimensions(get_obstacle_sprite(obstacle, state.frame_count))[0]
        for obstacle in state.obstacles
    )
    if rightmost + state.queued_gap <= screen_width:
        spawn_queued_pattern(state, screen_width)


def apply_roar_hits(state: GameState, frame_count: int) -> int:
    if state.roar_timer <= 0:
        return 0

    destroyed = 0
    surviving: list[Obstacle] = []
    for obstacle in state.obstacles:
        sprite = get_obstacle_sprite(obstacle, frame_count)
        width, _ = sprite_dimensions(sprite)
        in_range = obstacle.x <= DINO_X + ROAR_RANGE and obstacle.x + width >= DINO_X + 4
        if obstacle.spec.fragile and in_range:
            destroyed += 1
            continue
        surviving.append(obstacle)

    if destroyed:
        state.obstacles = surviving
        state.score += destroyed * ROAR_SCORE_BONUS
    return destroyed


def check_collisions(state: GameState, ground_y: int) -> bool:
    hero_box = get_hero_hitbox(state, ground_y)
    for obstacle in state.obstacles:
        obstacle_box = get_obstacle_hitbox(obstacle, state.frame_count, ground_y)
        if boxes_overlap(hero_box, obstacle_box):
            state.is_dead = True
            state.death_anim_frame = 0
            state.restart_delay = RESTART_DELAY_FRAMES
            if state.score > state.high_score:
                state.high_score = state.score
                state.high_score_dirty = True
            return True
    return False


def update_score(state: GameState, audio: AudioManager) -> None:
    state.score += 1
    if state.score > state.high_score:
        state.high_score = state.score
        state.high_score_dirty = True
        state.new_high_score = True
    if state.score % 100 == 0:
        state.score_flash_timer = SCORE_FLASH_FRAMES
        audio.play("checkpoint")


def update_difficulty(state: GameState, audio: AudioManager) -> None:
    target = speed_target(state.score)
    if state.speed < target:
        state.speed = min(target, state.speed + 0.02)

    next_biome = biome_for_score(state.score)
    if next_biome != state.current_biome:
        state.current_biome = next_biome
        state.banner_text = BIOME_LABELS[next_biome]
        state.banner_timer = BANNER_FRAMES
        audio.play("checkpoint")
    elif state.banner_timer > 0:
        state.banner_timer -= 1

    if state.roar_charge < ROAR_CHARGE_MAX:
        state.roar_charge = min(ROAR_CHARGE_MAX, state.roar_charge + ROAR_CHARGE_PER_FRAME + state.speed * 0.03)
    if state.roar_charge >= ROAR_CHARGE_MAX and not state.roar_ready_pinged:
        audio.play("roar_ready")
        state.roar_ready_pinged = True


def reset_state(state: GameState) -> None:
    high_score = state.high_score
    state.score = 0
    state.high_score = high_score
    state.speed = INITIAL_SPEED
    state.started = True
    state.is_dead = False
    state.is_paused = False
    state.frame_count = 0
    state.running_frames = 0
    state.is_jumping = False
    state.is_ducking = False
    state.dino_y = 0.0
    state.dino_vy = 0.0
    state.fast_falling = False
    state.duck_timer = 0
    state.obstacles.clear()
    state.ground_offset = 0.0
    state.ground_rough = False
    state.ground_segment_remaining = 0.0
    state.pattern_history.clear()
    state.last_pattern_name = None
    state.queued_pattern_name = None
    state.queued_gap = 0
    state.current_biome = "scrub"
    state.banner_text = BIOME_LABELS["scrub"]
    state.banner_timer = BANNER_FRAMES
    state.score_flash_timer = 0
    state.death_anim_frame = 0
    state.restart_delay = 0
    state.high_score_dirty = False
    state.new_high_score = False
    state.roar_charge = 0.0
    state.roar_timer = 0
    state.roar_ready_pinged = False


def init_colors() -> None:
    if not curses.has_colors():
        return
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)   # hero
    curses.init_pair(2, curses.COLOR_RED, -1)     # hit / game over
    curses.init_pair(3, curses.COLOR_CYAN, -1)    # UI / skyline
    curses.init_pair(4, curses.COLOR_YELLOW, -1)  # title / roar
    curses.init_pair(5, curses.COLOR_GREEN, -1)   # scrub hazards
    curses.init_pair(6, curses.COLOR_GREEN, -1)   # grove hazards
    curses.init_pair(7, curses.COLOR_WHITE, -1)   # basalt hazards


def biome_color_id(biome: str) -> int:
    return {"scrub": 5, "fossil": 6, "basalt": 7}[biome]


def tile_line(width: int, tile: str, offset: int) -> str:
    repeated = tile * ((width // len(tile)) + 4)
    start = offset % len(tile)
    return repeated[start : start + width - 1]


def render(stdscr, state: GameState, audio: AudioManager) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()

    if height < MIN_HEIGHT or width < MIN_WIDTH:
        message = f"Resize terminal (need {MIN_WIDTH}x{MIN_HEIGHT}, have {width}x{height})"
        safe_addstr(stdscr, height // 2, max(0, (width - len(message)) // 2), message)
        stdscr.refresh()
        return

    try:
        stdscr.bkgd(" ", 0)
    except curses.error:
        pass

    ground_y = height - 3
    has_color = curses.has_colors()

    if not state.started:
        render_skyline(stdscr, state, width, has_color)
        render_title(stdscr, state, audio, height, width, ground_y, has_color)
    else:
        render_skyline(stdscr, state, width, has_color)
        render_scoreboard(stdscr, state, width, has_color)
        render_roar_meter(stdscr, state, width, has_color)
        render_ground(stdscr, state, ground_y, width)
        render_obstacles(stdscr, state, ground_y, has_color)
        render_hero(stdscr, state, ground_y, has_color)
        render_banner(stdscr, state, width, has_color)
        if state.is_paused:
            render_pause_overlay(stdscr, height, width, has_color)
        if state.is_dead:
            state.death_anim_frame += 1
            render_game_over(stdscr, state, height, width, has_color)

    stdscr.refresh()


def render_title(stdscr, state: GameState, audio: AudioManager, height: int, width: int, ground_y: int, has_color: bool) -> None:
    title_attr = curses.color_pair(4) | curses.A_BOLD if has_color else curses.A_BOLD
    hero_attr = curses.color_pair(1) | curses.A_BOLD if has_color else curses.A_BOLD

    title = "D I N O   R U N"
    subtitle = "pick a dinosaur and run"
    safe_addstr(stdscr, 1, max(0, (width - len(title)) // 2), title, title_attr)
    safe_addstr(stdscr, 2, max(0, (width - len(subtitle)) // 2), subtitle, curses.A_DIM)

    selected_key = selected_dinosaur_key(state)
    selected_name = DINOSAUR_NAMES[selected_key]
    selected_blurb = DINOSAUR_BLURBS[selected_key]
    selected_index = DINOSAUR_ORDER.index(selected_key)
    picker_hint = f"{selected_index + 1}/{len(DINOSAUR_ORDER)}  {selected_name}"
    safe_addstr(stdscr, 3, max(0, (width - len(picker_hint)) // 2), picker_hint, title_attr)
    safe_addstr(stdscr, 4, max(0, (width - len(selected_blurb)) // 2), selected_blurb, curses.A_DIM)

    preview = get_title_preview_sprite(state)
    preview_x = max(0, (width - sprite_dimensions(preview)[0]) // 2)
    preview_y = 5
    draw_sprite(stdscr, preview, preview_y, preview_x, hero_attr)

    hooks = "Use \u2190/\u2192 or 1-0 to choose. Roar on X. Three biomes."
    hooks_y = preview_y + len(preview) + 1
    safe_addstr(stdscr, hooks_y, max(0, (width - len(hooks)) // 2), hooks, curses.A_DIM)

    cell_width = max(10, width // 5)
    roster_y = hooks_y + 1
    for index, key in enumerate(DINOSAUR_ORDER):
        row = index // 5
        col = index % 5
        number = "0" if index == 9 else str(index + 1)
        label = f"{number} {DINOSAUR_SHORT_NAMES[key]}"
        x = col * cell_width + max(0, (cell_width - len(label)) // 2)
        attr = title_attr if key == selected_key else curses.A_DIM
        safe_addstr(stdscr, roster_y + row, x, label, attr)

    start = "Press SPACE or ENTER to run"
    if (state.frame_count // 10) % 2:
        safe_addstr(stdscr, roster_y + 2, max(0, (width - len(start)) // 2), start, curses.A_BOLD)

    controls = "SPACE/UP jump  DOWN duck  X roar  P pause  Q/Esc quit"
    safe_addstr(stdscr, height - 2, max(0, (width - len(controls)) // 2), controls, curses.A_DIM)
    if audio.notice:
        safe_addstr(stdscr, height - 1, max(0, (width - len(audio.notice)) // 2), audio.notice, curses.A_DIM)

    render_ground(stdscr, state, ground_y, width)


def render_skyline(stdscr, state: GameState, width: int, has_color: bool) -> None:
    attr = curses.color_pair(3) if has_color else curses.A_DIM
    skyline = BIOME_SKYLINES[state.current_biome]
    for row, line in enumerate(skyline):
        safe_addstr(stdscr, 2 + row, max(0, (width - len(line)) // 2), line, attr)
    backdrop_attr = curses.color_pair(biome_color_id(state.current_biome)) | curses.A_DIM if has_color else curses.A_DIM
    backdrop = BIOME_BACKDROP_TILES[state.current_biome]
    offset_seed = int(state.ground_offset * 2)
    for row, tile in enumerate(backdrop):
        tiled = tile_line(width, tile, offset_seed + (row * 3))
        safe_addstr(stdscr, 6 + row, 0, tiled, backdrop_attr)


def render_scoreboard(stdscr, state: GameState, width: int, has_color: bool) -> None:
    if state.score_flash_timer > 0:
        state.score_flash_timer -= 1
        if state.score_flash_timer % 2 == 0:
            return
    score = f"{state.score:05d}"
    safe_addstr(stdscr, 1, width - len(score) - 2, score, curses.A_BOLD)
    if state.high_score > 0:
        hi = f"HI {state.high_score:05d}  "
        safe_addstr(stdscr, 1, width - len(score) - len(hi) - 2, hi, curses.A_DIM)
    biome = BIOME_LABELS[state.current_biome]
    safe_addstr(stdscr, 1, 2, biome, curses.A_DIM)


def render_roar_meter(stdscr, state: GameState, width: int, has_color: bool) -> None:
    filled = int((state.roar_charge / ROAR_CHARGE_MAX) * 12)
    bar = "[" + "█" * filled + "·" * (12 - filled) + "]"
    label = f"ROAR {bar}"
    attr = curses.color_pair(4) | curses.A_BOLD if has_color and state.roar_charge >= ROAR_CHARGE_MAX else curses.A_DIM
    safe_addstr(stdscr, 3, width - len(label) - 2, label, attr)


def render_ground(stdscr, state: GameState, ground_y: int, width: int) -> None:
    ground = BIOME_GROUNDS[state.current_biome]
    pattern = ground["rough"] if state.ground_rough else ground["flat"]
    state.ground_offset = (state.ground_offset + state.speed) % len(pattern)
    state.ground_segment_remaining -= state.speed
    if state.ground_segment_remaining <= 0:
        state.ground_rough = random.random() < 0.45
        state.ground_segment_remaining = len(pattern)
        pattern = ground["rough"] if state.ground_rough else ground["flat"]
    offset = int(state.ground_offset)
    repeated = pattern * ((width // len(pattern)) + 3)
    safe_addstr(stdscr, ground_y, 0, repeated[offset : offset + width - 1], curses.A_DIM)


def render_hero(stdscr, state: GameState, ground_y: int, has_color: bool) -> None:
    sprite = get_hero_sprite(state)
    draw_y = ground_y - len(sprite) + int(state.dino_y)
    attr = curses.color_pair(2 if state.is_dead else 1) | curses.A_BOLD if has_color else curses.A_BOLD
    draw_sprite(stdscr, sprite, draw_y, DINO_X, attr)


def render_obstacles(stdscr, state: GameState, ground_y: int, has_color: bool) -> None:
    for obstacle in state.obstacles:
        sprite = get_obstacle_sprite(obstacle, state.frame_count)
        draw_y = ground_y - len(sprite)
        if obstacle.spec.sprite_key == "scavenger":
            draw_y += obstacle.spec.bird_y_offset
        color = curses.color_pair(biome_color_id(obstacle.biome)) | curses.A_BOLD if has_color else curses.A_BOLD
        draw_sprite(stdscr, sprite, draw_y, int(obstacle.x), color)


def render_banner(stdscr, state: GameState, width: int, has_color: bool) -> None:
    if state.banner_timer <= 0:
        return
    attr = curses.color_pair(4) | curses.A_BOLD if has_color else curses.A_BOLD
    safe_addstr(stdscr, 5, max(0, (width - len(state.banner_text)) // 2), state.banner_text, attr)


def render_pause_overlay(stdscr, height: int, width: int, has_color: bool) -> None:
    attr = curses.color_pair(4) | curses.A_BOLD if has_color else curses.A_BOLD
    safe_addstr(stdscr, height // 2 - 1, max(0, (width - 6) // 2), "Paused", attr)
    safe_addstr(stdscr, height // 2, max(0, (width - 18) // 2), "Press P to resume", curses.A_DIM)


def render_game_over(stdscr, state: GameState, height: int, width: int, has_color: bool) -> None:
    title = "G A M E   O V E R"
    score = f"Score: {state.score:05d}"
    best = f"Best:  {state.high_score:05d}"
    restart = "Press ENTER or SPACE to retry"
    attr = curses.color_pair(2) | curses.A_BOLD if has_color else curses.A_BOLD
    safe_addstr(stdscr, height // 2 - 2, max(0, (width - len(title)) // 2), title, attr)
    safe_addstr(stdscr, height // 2, max(0, (width - len(score)) // 2), score, curses.A_BOLD)
    safe_addstr(stdscr, height // 2 + 1, max(0, (width - len(best)) // 2), best, curses.A_BOLD)
    if state.new_high_score:
        safe_addstr(stdscr, height // 2 + 2, max(0, (width - 16) // 2), "*** NEW BEST ***", curses.A_DIM)
    if (state.death_anim_frame // 10) % 2 == 0:
        safe_addstr(stdscr, height // 2 + 4, max(0, (width - len(restart)) // 2), restart, curses.A_DIM)


def main(stdscr) -> None:
    try:
        curses.curs_set(0)
    except curses.error:
        pass

    stdscr.nodelay(True)
    stdscr.timeout(0)
    init_colors()

    state = GameState(high_score=load_high_score())
    audio = AudioManager()
    rng = random.Random()

    try:
        while True:
            frame_start = time.monotonic()
            state.frame_count += 1

            height, width = stdscr.getmaxyx()
            ground_y = height - 3

            action = handle_input(stdscr, state, audio)
            if action == "quit":
                if state.high_score_dirty:
                    try:
                        save_high_score(state.high_score)
                    except OSError:
                        pass
                break
            if action == "restart":
                reset_state(state)

            if state.started and not state.is_dead and not state.is_paused:
                state.running_frames += 1
                update_physics(state, audio)
                update_obstacles(state, width, rng)
                if apply_roar_hits(state, state.frame_count):
                    state.score_flash_timer = SCORE_FLASH_FRAMES
                died = check_collisions(state, ground_y)
                if died:
                    audio.play("hit")
                    if state.high_score_dirty:
                        try:
                            save_high_score(state.high_score)
                        except OSError:
                            pass
                        state.high_score_dirty = False
                else:
                    update_score(state, audio)
                    update_difficulty(state, audio)

            render(stdscr, state, audio)

            elapsed = time.monotonic() - frame_start
            sleep_ms = max(1, int((FRAME_TIME - elapsed) * 1000))
            curses.napms(sleep_ms)
    finally:
        audio.stop()


def run() -> None:
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    print("Thanks for playing Dino Run!")
