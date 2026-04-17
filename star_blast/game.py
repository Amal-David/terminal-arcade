"""Star Blast — a Nokia-inspired terminal shooter."""

from __future__ import annotations

import curses
import random
import time
from dataclasses import dataclass, field

from .storage import load_scores, save_scores

FPS = 20
FRAME_TIME = 1.0 / FPS

MIN_WIDTH = 72
MIN_HEIGHT = 24

PLAYER_X = 4
SHOT_COOLDOWN_FRAMES = 4
INVULNERABILITY_FRAMES = 24
LEVEL_CLEAR_BONUS = 100

MODE_CAMPAIGN = "campaign"
MODE_ENDLESS = "endless"

MOVE_UP_KEYS = {curses.KEY_UP, ord("w"), ord("W")}
MOVE_DOWN_KEYS = {curses.KEY_DOWN, ord("s"), ord("S")}
FIRE_KEYS = {ord(" ")}
PAUSE_KEYS = {ord("p"), ord("P")}
QUIT_KEYS = {ord("q"), ord("Q"), 27}
RESTART_KEYS = {ord("r"), ord("R"), ord(" "), curses.KEY_ENTER, 10, 13}
TITLE_LEFT_KEYS = {curses.KEY_LEFT, ord("a"), ord("A")}
TITLE_RIGHT_KEYS = {curses.KEY_RIGHT, ord("d"), ord("D")}
TITLE_MODE_KEYS = {
    ord("1"): MODE_CAMPAIGN,
    ord("2"): MODE_ENDLESS,
}

MODE_LABELS = {
    MODE_CAMPAIGN: "Campaign",
    MODE_ENDLESS: "Endless",
}

TITLE_ART = [
    "  ███████╗████████╗ █████╗ ██████╗     ██████╗ ██╗      █████╗ ███████╗████████╗",
    "  ██╔════╝╚══██╔══╝██╔══██╗██╔══██╗    ██╔══██╗██║     ██╔══██╗██╔════╝╚══██╔══╝",
    "  ███████╗   ██║   ███████║██████╔╝    ██████╔╝██║     ███████║███████╗   ██║   ",
    "  ╚════██║   ██║   ██╔══██║██╔══██╗    ██╔══██╗██║     ██╔══██║╚════██║   ██║   ",
    "  ███████║   ██║   ██║  ██║██║  ██║    ██████╔╝███████╗██║  ██║███████║   ██║   ",
    "  ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝    ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝   ╚═╝   ",
]


@dataclass(frozen=True)
class EnemySpec:
    glyph: str
    hp: int
    speed: float
    score: int
    width: int = 1
    shoots: bool = False


ENEMY_SPECS = {
    "debris": EnemySpec(glyph="*", hp=1, speed=0.65, score=10),
    "scout": EnemySpec(glyph=">", hp=1, speed=0.90, score=20),
    "zigzag": EnemySpec(glyph="Z", hp=1, speed=0.75, score=20),
    "turret": EnemySpec(glyph="H", hp=3, speed=0.35, score=50, shoots=True),
    "carrier": EnemySpec(glyph="<M>", hp=10, speed=0.40, score=250, width=3, shoots=True),
}


@dataclass(frozen=True)
class SpawnRule:
    kind: str
    interval: int
    start: int
    end: int


@dataclass(frozen=True)
class StageConfig:
    name: str
    wave_duration: int
    boss_hp: int
    rules: tuple[SpawnRule, ...]


STAGES = [
    StageConfig(
        name="Meteor Belt",
        wave_duration=260,
        boss_hp=10,
        rules=(
            SpawnRule("debris", 24, 20, 220),
            SpawnRule("scout", 52, 80, 240),
        ),
    ),
    StageConfig(
        name="Ambush Line",
        wave_duration=320,
        boss_hp=14,
        rules=(
            SpawnRule("scout", 34, 16, 280),
            SpawnRule("zigzag", 56, 70, 300),
            SpawnRule("turret", 118, 150, 290),
        ),
    ),
    StageConfig(
        name="Final Orbit",
        wave_duration=380,
        boss_hp=18,
        rules=(
            SpawnRule("debris", 22, 15, 320),
            SpawnRule("scout", 28, 20, 350),
            SpawnRule("zigzag", 42, 40, 350),
            SpawnRule("turret", 94, 90, 340),
        ),
    ),
]


@dataclass
class Bullet:
    x: float
    y: int
    dx: float
    friendly: bool


@dataclass
class Enemy:
    kind: str
    x: float
    y: int
    hp: int
    width: int = 1
    direction: int = 1
    phase: int = 0
    fire_timer: int = 0


@dataclass
class GameState:
    selected_mode: str = MODE_CAMPAIGN
    mode: str = MODE_CAMPAIGN
    screen: str = "title"
    score: int = 0
    lives: int = 3
    player_y: int = 0
    player_invuln: int = 0
    shot_cooldown: int = 0
    bullets: list[Bullet] = field(default_factory=list)
    enemy_bullets: list[Bullet] = field(default_factory=list)
    enemies: list[Enemy] = field(default_factory=list)
    paused: bool = False
    running: bool = True
    frame_count: int = 0
    stage_index: int = 0
    stage_frame: int = 0
    boss_spawned: bool = False
    endless_wave: int = 1
    campaign_high_score: int = 0
    endless_high_score: int = 0
    high_score_dirty: bool = False
    banner_text: str = ""
    banner_timer: int = 0
    result_text: str = ""
    result_hint: str = ""


def clamp_player_y(current: int, delta: int, field_h: int) -> int:
    """Move the player while keeping them inside the playfield."""
    return max(0, min(field_h - 1, current + delta))


def endless_wave_for_score(score: int) -> int:
    """Map score to endless wave difficulty."""
    return max(1, score // 180 + 1)


def available_endless_kinds(wave: int) -> list[str]:
    """Return the enemy kinds available for an endless wave."""
    kinds = ["debris", "scout"]
    if wave >= 3:
        kinds.append("zigzag")
    if wave >= 5:
        kinds.append("turret")
    return kinds


def endless_spawn_interval(wave: int) -> int:
    """Spawn enemies faster as the endless wave increases."""
    return max(12, 32 - wave * 2)


def compute_playfield(term_h: int, term_w: int) -> tuple[int, int, int, int]:
    """Compute the playfield box inside the terminal."""
    ox = 2
    oy = 3
    field_w = term_w - 6
    field_h = term_h - 8
    return ox, oy, field_w, field_h


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
    text = text[:max_len]
    try:
        stdscr.addstr(y, x, text, attr)
    except curses.error:
        pass


def init_colors() -> bool:
    if not curses.has_colors():
        return False
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_YELLOW, -1)
    curses.init_pair(3, curses.COLOR_RED, -1)
    curses.init_pair(4, curses.COLOR_GREEN, -1)
    curses.init_pair(5, curses.COLOR_WHITE, -1)
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)
    return True


def spawn_enemy(kind: str, field_w: int, field_h: int, rng: random.Random, hp_override: int | None = None) -> Enemy:
    """Create a new enemy at the right edge of the playfield."""
    spec = ENEMY_SPECS[kind]
    y = field_h // 2 if kind == "carrier" else rng.randint(0, max(0, field_h - 1))
    fire_timer = 0
    if kind == "turret":
        fire_timer = 32 + rng.randint(0, 12)
    elif kind == "carrier":
        fire_timer = 18
    return Enemy(
        kind=kind,
        x=float(field_w - spec.width - 1),
        y=y,
        hp=hp_override if hp_override is not None else spec.hp,
        width=spec.width,
        fire_timer=fire_timer,
    )


def start_game(state: GameState, field_h: int) -> None:
    """Reset state for a new run using the selected mode."""
    state.mode = state.selected_mode
    state.screen = "playing"
    state.score = 0
    state.lives = 3
    state.player_y = field_h // 2
    state.player_invuln = 0
    state.shot_cooldown = 0
    state.bullets.clear()
    state.enemy_bullets.clear()
    state.enemies.clear()
    state.paused = False
    state.frame_count = 0
    state.stage_index = 0
    state.stage_frame = 0
    state.boss_spawned = False
    state.endless_wave = 1
    state.result_text = ""
    state.result_hint = ""
    if state.mode == MODE_CAMPAIGN:
        state.banner_text = f"Stage 1: {STAGES[0].name}"
    else:
        state.banner_text = "Endless Wave 1"
    state.banner_timer = 40


def record_high_score(state: GameState) -> None:
    """Track the best score for the active mode."""
    if state.mode == MODE_CAMPAIGN and state.score > state.campaign_high_score:
        state.campaign_high_score = state.score
        state.high_score_dirty = True
    elif state.mode == MODE_ENDLESS and state.score > state.endless_high_score:
        state.endless_high_score = state.score
        state.high_score_dirty = True


def finish_session(state: GameState, screen: str, result_text: str) -> None:
    """Finish the current session and keep the best score."""
    state.screen = screen
    state.paused = False
    state.result_text = result_text
    state.result_hint = "Press SPACE, ENTER, or R to return to the title"
    state.banner_timer = 0
    record_high_score(state)


def advance_campaign_if_needed(state: GameState) -> None:
    """Advance campaign stages once a boss has been defeated."""
    if state.mode != MODE_CAMPAIGN or not state.boss_spawned:
        return
    if any(enemy.kind == "carrier" and enemy.hp > 0 for enemy in state.enemies):
        return

    if state.stage_index >= len(STAGES) - 1:
        finish_session(state, "cleared", "Campaign clear")
        return

    state.stage_index += 1
    state.stage_frame = 0
    state.boss_spawned = False
    state.enemies.clear()
    state.bullets.clear()
    state.enemy_bullets.clear()
    state.banner_text = f"Stage {state.stage_index + 1}: {STAGES[state.stage_index].name}"
    state.banner_timer = 40


def _enemy_hit(enemy: Enemy, bullet: Bullet) -> bool:
    bx = int(round(bullet.x))
    ex = int(round(enemy.x))
    return bullet.y == enemy.y and ex <= bx < ex + enemy.width


def _player_hit_by_enemy(enemy: Enemy, player_y: int) -> bool:
    ex = int(round(enemy.x))
    return enemy.y == player_y and ex <= PLAYER_X < ex + enemy.width


def handle_player_hit(state: GameState, field_h: int) -> None:
    """Apply player damage and respawn or end the run."""
    if state.player_invuln > 0:
        return

    state.lives -= 1
    state.player_invuln = INVULNERABILITY_FRAMES
    state.player_y = field_h // 2
    state.enemy_bullets.clear()
    state.bullets.clear()
    state.enemies = [enemy for enemy in state.enemies if enemy.x > PLAYER_X + 3]

    if state.lives <= 0:
        finish_session(state, "gameover", "Ship destroyed")


def resolve_collisions(state: GameState, field_h: int) -> None:
    """Resolve projectile and ship collisions."""
    remaining_bullets: list[Bullet] = []
    boss_defeated = False

    for bullet in state.bullets:
        hit_enemy = None
        for enemy in state.enemies:
            if enemy.hp <= 0:
                continue
            if _enemy_hit(enemy, bullet):
                hit_enemy = enemy
                break

        if hit_enemy is None:
            remaining_bullets.append(bullet)
            continue

        hit_enemy.hp -= 1
        if hit_enemy.hp <= 0:
            state.score += ENEMY_SPECS[hit_enemy.kind].score
            if hit_enemy.kind == "carrier":
                state.score += LEVEL_CLEAR_BONUS
                boss_defeated = True
            record_high_score(state)

    state.bullets = remaining_bullets
    state.enemies = [enemy for enemy in state.enemies if enemy.hp > 0]

    player_hit = False
    surviving_enemy_bullets: list[Bullet] = []
    for bullet in state.enemy_bullets:
        if int(round(bullet.x)) == PLAYER_X and bullet.y == state.player_y and state.player_invuln == 0:
            player_hit = True
            continue
        surviving_enemy_bullets.append(bullet)
    state.enemy_bullets = surviving_enemy_bullets

    if not player_hit and state.player_invuln == 0:
        for enemy in state.enemies:
            if _player_hit_by_enemy(enemy, state.player_y):
                player_hit = True
                break

    if player_hit:
        handle_player_hit(state, field_h)

    if boss_defeated:
        advance_campaign_if_needed(state)


def _move_bullets(bullets: list[Bullet], field_w: int) -> list[Bullet]:
    moved: list[Bullet] = []
    for bullet in bullets:
        bullet.x += bullet.dx
        if 0 <= bullet.x < field_w:
            moved.append(bullet)
    return moved


def update_enemies(state: GameState, field_w: int, field_h: int) -> None:
    """Advance enemy positions and fire enemy projectiles."""
    spawned_enemy_bullets: list[Bullet] = []

    for enemy in state.enemies:
        spec = ENEMY_SPECS[enemy.kind]
        if enemy.kind == "zigzag":
            enemy.x -= spec.speed
            enemy.phase += 1
            if enemy.phase % 3 == 0:
                enemy.y += enemy.direction
                if enemy.y <= 0 or enemy.y >= field_h - 1:
                    enemy.direction *= -1
                    enemy.y = max(0, min(field_h - 1, enemy.y))
        elif enemy.kind == "turret":
            enemy.x -= spec.speed
            enemy.fire_timer -= 1
            if enemy.fire_timer <= 0 and enemy.x < field_w - 8:
                spawned_enemy_bullets.append(Bullet(x=enemy.x - 1, y=enemy.y, dx=-1.0, friendly=False))
                enemy.fire_timer = 36
        elif enemy.kind == "carrier":
            target_x = max(field_w - 12, field_w // 2)
            if enemy.x > target_x:
                enemy.x -= spec.speed
            enemy.phase += 1
            if enemy.phase % 2 == 0:
                enemy.y += enemy.direction
                if enemy.y <= 1 or enemy.y >= field_h - 2:
                    enemy.direction *= -1
                    enemy.y = max(1, min(field_h - 2, enemy.y))
            enemy.fire_timer -= 1
            if enemy.fire_timer <= 0:
                for delta in (-1, 0, 1):
                    shot_y = max(0, min(field_h - 1, enemy.y + delta))
                    spawned_enemy_bullets.append(Bullet(x=enemy.x - 1, y=shot_y, dx=-1.0, friendly=False))
                enemy.fire_timer = 22
        else:
            enemy.x -= spec.speed

    state.enemies = [enemy for enemy in state.enemies if enemy.x + enemy.width > 0]
    state.enemy_bullets.extend(spawned_enemy_bullets)


def spawn_for_mode(state: GameState, field_w: int, field_h: int, rng: random.Random) -> None:
    """Spawn enemies for the current mode."""
    if state.mode == MODE_CAMPAIGN:
        stage = STAGES[state.stage_index]
        if not state.boss_spawned:
            for rule in stage.rules:
                if rule.start <= state.stage_frame <= rule.end and state.stage_frame % rule.interval == 0:
                    state.enemies.append(spawn_enemy(rule.kind, field_w, field_h, rng))

            if state.stage_frame >= stage.wave_duration:
                state.enemies.append(spawn_enemy("carrier", field_w, field_h, rng, hp_override=stage.boss_hp))
                state.boss_spawned = True
        return

    state.endless_wave = endless_wave_for_score(state.score)
    wave = state.endless_wave
    if state.banner_text != f"Endless Wave {wave}" and wave > 1 and state.frame_count % 20 == 0:
        state.banner_text = f"Endless Wave {wave}"
        state.banner_timer = 24
    if state.frame_count % endless_spawn_interval(wave) == 0:
        kind = rng.choice(available_endless_kinds(wave))
        state.enemies.append(spawn_enemy(kind, field_w, field_h, rng))


def update(state: GameState, field_w: int, field_h: int, rng: random.Random) -> None:
    """Advance one gameplay frame."""
    if state.screen != "playing" or state.paused:
        return

    state.frame_count += 1
    state.stage_frame += 1

    if state.shot_cooldown > 0:
        state.shot_cooldown -= 1
    if state.player_invuln > 0:
        state.player_invuln -= 1
    if state.banner_timer > 0:
        state.banner_timer -= 1

    spawn_for_mode(state, field_w, field_h, rng)
    update_enemies(state, field_w, field_h)
    state.bullets = _move_bullets(state.bullets, field_w)
    state.enemy_bullets = _move_bullets(state.enemy_bullets, field_w)
    resolve_collisions(state, field_h)


def handle_input(stdscr, state: GameState, field_h: int) -> str | None:
    """Consume queued input and update state."""
    keys: list[int] = []
    while True:
        key = stdscr.getch()
        if key == -1:
            break
        keys.append(key)

    if any(key in QUIT_KEYS for key in keys):
        return "quit"

    if state.screen == "title":
        for key in keys:
            if key in TITLE_LEFT_KEYS:
                state.selected_mode = MODE_ENDLESS if state.selected_mode == MODE_CAMPAIGN else MODE_CAMPAIGN
            elif key in TITLE_RIGHT_KEYS:
                state.selected_mode = MODE_ENDLESS if state.selected_mode == MODE_CAMPAIGN else MODE_CAMPAIGN
            elif key in TITLE_MODE_KEYS:
                state.selected_mode = TITLE_MODE_KEYS[key]
        if any(key in RESTART_KEYS for key in keys):
            start_game(state, field_h)
        return None

    if state.screen in {"gameover", "cleared"}:
        if any(key in RESTART_KEYS for key in keys):
            state.screen = "title"
            state.paused = False
        return None

    if any(key in PAUSE_KEYS for key in keys):
        state.paused = not state.paused
        return None

    if state.paused:
        return None

    if any(key in MOVE_UP_KEYS for key in keys):
        state.player_y = clamp_player_y(state.player_y, -1, field_h)
    if any(key in MOVE_DOWN_KEYS for key in keys):
        state.player_y = clamp_player_y(state.player_y, 1, field_h)
    if any(key in FIRE_KEYS for key in keys) and state.shot_cooldown == 0:
        state.bullets.append(Bullet(x=float(PLAYER_X + 1), y=state.player_y, dx=1.6, friendly=True))
        state.shot_cooldown = SHOT_COOLDOWN_FRAMES
    return None


def _draw_border(stdscr, ox: int, oy: int, field_w: int, field_h: int, attr: int) -> None:
    safe_addstr(stdscr, oy, ox, "╔" + "═" * field_w + "╗", attr)
    for row in range(field_h):
        safe_addstr(stdscr, oy + 1 + row, ox, "║", attr)
        safe_addstr(stdscr, oy + 1 + row, ox + field_w + 1, "║", attr)
    safe_addstr(stdscr, oy + field_h + 1, ox, "╚" + "═" * field_w + "╝", attr)


def render_title(stdscr, state: GameState, height: int, width: int, has_color: bool) -> None:
    title_attr = curses.color_pair(2) | curses.A_BOLD if has_color else curses.A_BOLD
    accent_attr = curses.color_pair(1) | curses.A_BOLD if has_color else curses.A_BOLD
    selected_attr = (curses.color_pair(1) | curses.A_REVERSE | curses.A_BOLD) if has_color else (curses.A_REVERSE | curses.A_BOLD)
    dim_attr = curses.A_DIM

    y = max(1, (height - 18) // 2)
    for line in TITLE_ART:
        safe_addstr(stdscr, y, max(0, (width - len(line)) // 2), line, title_attr)
        y += 1

    y += 1
    subtitle = "Nokia-inspired side-scrolling shooter"
    safe_addstr(stdscr, y, max(0, (width - len(subtitle)) // 2), subtitle, dim_attr)
    y += 2

    modes = [
        (MODE_CAMPAIGN, f"[1] Campaign  HI {state.campaign_high_score}"),
        (MODE_ENDLESS, f"[2] Endless   HI {state.endless_high_score}"),
    ]
    for mode, label in modes:
        attr = selected_attr if state.selected_mode == mode else accent_attr
        safe_addstr(stdscr, y, max(0, (width - len(label)) // 2), label, attr)
        y += 2

    if state.selected_mode == MODE_CAMPAIGN:
        blurb = "Three short stages, escalating enemy waves, and a carrier boss at the end of every level."
    else:
        blurb = "Survive forever as enemy variety and spawn pressure ramp up with your score."
    safe_addstr(stdscr, y, max(0, (width - len(blurb)) // 2), blurb, dim_attr)

    controls = "A/D or ←/→ change mode   SPACE or ENTER launch   Q or Esc quit"
    safe_addstr(stdscr, height - 2, max(0, (width - len(controls)) // 2), controls, dim_attr)


def render_playfield(stdscr, state: GameState, has_color: bool) -> None:
    height, width = stdscr.getmaxyx()
    ox, oy, field_w, field_h = compute_playfield(height, width)

    border_attr = curses.color_pair(5) if has_color else curses.A_DIM
    hud_attr = curses.color_pair(4) | curses.A_BOLD if has_color else curses.A_BOLD
    player_attr = curses.color_pair(1) | curses.A_BOLD if has_color else curses.A_BOLD
    bullet_attr = curses.color_pair(2) | curses.A_BOLD if has_color else curses.A_BOLD
    enemy_attr = curses.color_pair(3) | curses.A_BOLD if has_color else curses.A_BOLD
    boss_attr = curses.color_pair(6) | curses.A_BOLD if has_color else curses.A_BOLD

    mode_text = MODE_LABELS[state.mode]
    phase_text = f"Stage {state.stage_index + 1}/3" if state.mode == MODE_CAMPAIGN else f"Wave {state.endless_wave}"
    hi_score = state.campaign_high_score if state.mode == MODE_CAMPAIGN else state.endless_high_score

    _draw_border(stdscr, ox, oy, field_w, field_h, border_attr)
    safe_addstr(stdscr, oy - 2, ox + 1, f"Score: {state.score}", hud_attr)
    safe_addstr(stdscr, oy - 2, ox + 18, f"Lives: {state.lives}", hud_attr)
    safe_addstr(stdscr, oy - 2, ox + 34, f"Mode: {mode_text}", hud_attr)
    safe_addstr(stdscr, oy - 2, ox + 54, phase_text, hud_attr)
    safe_addstr(stdscr, oy - 2, ox + field_w - 10, f"HI {hi_score}", hud_attr)

    if state.player_invuln == 0 or state.player_invuln % 4 < 2:
        safe_addstr(stdscr, oy + 1 + state.player_y, ox + 1 + PLAYER_X, ">", player_attr)

    for bullet in state.bullets:
        safe_addstr(stdscr, oy + 1 + bullet.y, ox + 1 + int(round(bullet.x)), "-", bullet_attr)
    for bullet in state.enemy_bullets:
        safe_addstr(stdscr, oy + 1 + bullet.y, ox + 1 + int(round(bullet.x)), "<", enemy_attr)

    for enemy in state.enemies:
        attr = boss_attr if enemy.kind == "carrier" else enemy_attr
        safe_addstr(
            stdscr,
            oy + 1 + enemy.y,
            ox + 1 + int(round(enemy.x)),
            ENEMY_SPECS[enemy.kind].glyph,
            attr,
        )

    if state.banner_timer > 0 and state.banner_text:
        safe_addstr(stdscr, oy + field_h + 2, max(0, (width - len(state.banner_text)) // 2), state.banner_text, hud_attr)


def render_overlay(stdscr, title: str, hint: str, has_color: bool) -> None:
    attr = curses.color_pair(2) | curses.A_BOLD if has_color else curses.A_BOLD
    safe_addstr(stdscr, curses.LINES // 2 - 1, max(0, (curses.COLS - len(title)) // 2), title, attr)
    safe_addstr(stdscr, curses.LINES // 2 + 1, max(0, (curses.COLS - len(hint)) // 2), hint, curses.A_DIM)


def render_small_terminal(stdscr, height: int, width: int) -> None:
    stdscr.erase()
    msg = f"Terminal too small ({width}x{height}). Need {MIN_WIDTH}x{MIN_HEIGHT}."
    hint = "Resize the terminal for Star Blast. Press Q or Esc to quit."
    safe_addstr(stdscr, height // 2 - 1, max(0, (width - len(msg)) // 2), msg, curses.A_BOLD)
    safe_addstr(stdscr, height // 2 + 1, max(0, (width - len(hint)) // 2), hint, curses.A_DIM)
    stdscr.refresh()


def render(stdscr, state: GameState, has_color: bool) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    if height < MIN_HEIGHT or width < MIN_WIDTH:
        render_small_terminal(stdscr, height, width)
        return

    if state.screen == "title":
        render_title(stdscr, state, height, width, has_color)
    else:
        render_playfield(stdscr, state, has_color)
        if state.paused:
            render_overlay(stdscr, "P A U S E D", "Press P to resume", has_color)
        elif state.screen == "gameover":
            render_overlay(stdscr, state.result_text, state.result_hint, has_color)
        elif state.screen == "cleared":
            render_overlay(stdscr, state.result_text, state.result_hint, has_color)

    stdscr.refresh()


def main(stdscr) -> None:
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.nodelay(True)
    stdscr.timeout(0)
    has_color = init_colors()

    scores = load_scores()
    state = GameState(
        campaign_high_score=scores["campaign_high_score"],
        endless_high_score=scores["endless_high_score"],
    )
    rng = random.Random()

    while state.running:
        frame_start = time.monotonic()
        height, width = stdscr.getmaxyx()

        if height >= MIN_HEIGHT and width >= MIN_WIDTH and state.player_y == 0 and state.screen == "title":
            _, _, _, field_h = compute_playfield(height, width)
            state.player_y = field_h // 2

        if height < MIN_HEIGHT or width < MIN_WIDTH:
            render(stdscr, state, has_color)
            action = handle_input(stdscr, state, 1)
            if action == "quit":
                break
            curses.napms(50)
            continue

        _, _, field_w, field_h = compute_playfield(height, width)
        action = handle_input(stdscr, state, field_h)
        if action == "quit":
            record_high_score(state)
            break

        update(state, field_w, field_h, rng)
        render(stdscr, state, has_color)

        elapsed = time.monotonic() - frame_start
        sleep_ms = max(1, int((FRAME_TIME - elapsed) * 1000))
        curses.napms(sleep_ms)

    if state.high_score_dirty:
        save_scores(
            {
                "campaign_high_score": state.campaign_high_score,
                "endless_high_score": state.endless_high_score,
            }
        )


def run() -> None:
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
