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

PLAYER_GLYPH = "/A\\"
PLAYER_WIDTH = len(PLAYER_GLYPH)
PLAYER_STRAFE_STEP = 2
SHOT_COOLDOWN_FRAMES = 4
FIRE_HOLD_FRAMES = 3
INVULNERABILITY_FRAMES = 24
LEVEL_CLEAR_BONUS = 100
PLAYFIELD_MIN_WIDTH = 34
PLAYFIELD_MAX_WIDTH = 40
PLAYFIELD_MIN_HEIGHT = 15
PLAYFIELD_MAX_HEIGHT = 18

MODE_CAMPAIGN = "campaign"
MODE_ENDLESS = "endless"

MOVE_LEFT_KEYS = {curses.KEY_LEFT, ord("a"), ord("A")}
MOVE_RIGHT_KEYS = {curses.KEY_RIGHT, ord("d"), ord("D")}
FIRE_KEYS = {ord(" ")}
AUTOFIRE_TOGGLE_KEYS = {ord("f"), ord("F")}
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
    width: int
    shoots: bool = False


ENEMY_SPECS = {
    "debris": EnemySpec(glyph="[#]", hp=1, speed=0.55, score=10, width=3),
    "scout": EnemySpec(glyph="[V]", hp=1, speed=0.75, score=20, width=3),
    "zigzag": EnemySpec(glyph="<W>", hp=1, speed=0.62, score=20, width=3),
    "turret": EnemySpec(glyph="[###]", hp=3, speed=0.34, score=50, width=5, shoots=True),
    "carrier": EnemySpec(glyph="/MMM\\", hp=10, speed=0.28, score=250, width=5, shoots=True),
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
            SpawnRule("debris", 22, 10, 220),
            SpawnRule("scout", 48, 70, 240),
        ),
    ),
    StageConfig(
        name="Ambush Line",
        wave_duration=320,
        boss_hp=14,
        rules=(
            SpawnRule("scout", 32, 16, 280),
            SpawnRule("zigzag", 52, 70, 300),
            SpawnRule("turret", 112, 150, 290),
        ),
    ),
    StageConfig(
        name="Final Orbit",
        wave_duration=380,
        boss_hp=18,
        rules=(
            SpawnRule("debris", 20, 15, 320),
            SpawnRule("scout", 26, 20, 350),
            SpawnRule("zigzag", 40, 40, 350),
            SpawnRule("turret", 88, 90, 340),
        ),
    ),
]


@dataclass
class Bullet:
    x: float
    y: float
    dy: float
    friendly: bool


@dataclass
class Enemy:
    kind: str
    x: float
    y: float
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
    player_x: int = 0
    player_invuln: int = 0
    shot_cooldown: int = 0
    fire_hold_frames: int = 0
    autofire_enabled: bool = False
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


def clamp_player_x(current: int, delta: int, field_w: int) -> int:
    """Move the player while keeping the starship inside the playfield."""
    return max(0, min(field_w - PLAYER_WIDTH, current + delta))


def player_row(field_h: int) -> int:
    """Bottom row where the player ship sits."""
    return max(0, field_h - 2)


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
    """Compute a compact centered playfield for keyboard movement."""
    field_w = max(PLAYFIELD_MIN_WIDTH, min(term_w - 20, PLAYFIELD_MAX_WIDTH))
    field_h = max(PLAYFIELD_MIN_HEIGHT, min(term_h - 8, PLAYFIELD_MAX_HEIGHT))
    ox = max(1, (term_w - (field_w + 2)) // 2)
    oy = max(2, (term_h - (field_h + 2)) // 2 - 1)
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
    """Create a new enemy at the top edge of the playfield."""
    spec = ENEMY_SPECS[kind]
    x = max(0, min(field_w - spec.width, rng.randint(0, max(0, field_w - spec.width))))
    fire_timer = 0
    if kind == "turret":
        fire_timer = 28 + rng.randint(0, 14)
    elif kind == "carrier":
        x = max(0, field_w // 2 - spec.width // 2)
        fire_timer = 18
    return Enemy(
        kind=kind,
        x=float(x),
        y=0.0,
        hp=hp_override if hp_override is not None else spec.hp,
        width=spec.width,
        fire_timer=fire_timer,
    )


def start_game(state: GameState, field_w: int) -> None:
    """Reset state for a new run using the selected mode."""
    state.mode = state.selected_mode
    state.screen = "playing"
    state.score = 0
    state.lives = 3
    state.player_x = max(0, field_w // 2 - PLAYER_WIDTH // 2)
    state.player_invuln = 0
    state.shot_cooldown = 0
    state.fire_hold_frames = 0
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
    ey = int(round(enemy.y))
    by = int(round(bullet.y))
    return by == ey and ex <= bx < ex + enemy.width


def _player_hit_by_enemy(enemy: Enemy, player_x: int, field_h: int) -> bool:
    ex = int(round(enemy.x))
    ey = int(round(enemy.y))
    py = player_row(field_h)
    return ey >= py and ex < player_x + PLAYER_WIDTH and player_x < ex + enemy.width


def handle_player_hit(state: GameState, field_w: int, field_h: int) -> None:
    """Apply player damage and respawn or end the run."""
    if state.player_invuln > 0:
        return

    state.lives -= 1
    state.player_invuln = INVULNERABILITY_FRAMES
    state.player_x = max(0, field_w // 2 - PLAYER_WIDTH // 2)
    state.enemy_bullets.clear()
    state.bullets.clear()
    state.enemies = [enemy for enemy in state.enemies if enemy.y < field_h - 5]

    if state.lives <= 0:
        finish_session(state, "gameover", "Ship destroyed")


def resolve_collisions(state: GameState, field_w: int, field_h: int) -> None:
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
    py = player_row(field_h)
    surviving_enemy_bullets: list[Bullet] = []
    for bullet in state.enemy_bullets:
        bx = int(round(bullet.x))
        by = int(round(bullet.y))
        if state.player_invuln == 0 and by >= py and state.player_x <= bx < state.player_x + PLAYER_WIDTH:
            player_hit = True
            continue
        surviving_enemy_bullets.append(bullet)
    state.enemy_bullets = surviving_enemy_bullets

    if not player_hit and state.player_invuln == 0:
        for enemy in state.enemies:
            if _player_hit_by_enemy(enemy, state.player_x, field_h):
                player_hit = True
                break

    if player_hit:
        handle_player_hit(state, field_w, field_h)

    if boss_defeated:
        advance_campaign_if_needed(state)


def fire_player_shot(state: GameState, field_h: int) -> None:
    """Spawn one player shot from the starship nose."""
    state.bullets.append(
        Bullet(
            x=float(state.player_x + PLAYER_WIDTH // 2),
            y=float(player_row(field_h) - 1),
            dy=-1.6,
            friendly=True,
        )
    )
    state.shot_cooldown = SHOT_COOLDOWN_FRAMES


def toggle_autofire(state: GameState) -> None:
    """Toggle the continuous-fire assist and surface it in the HUD banner."""
    state.autofire_enabled = not state.autofire_enabled
    state.banner_text = "Autofire ON" if state.autofire_enabled else "Autofire OFF"
    state.banner_timer = 20


def _move_bullets(bullets: list[Bullet], field_h: int) -> list[Bullet]:
    moved: list[Bullet] = []
    for bullet in bullets:
        bullet.y += bullet.dy
        if 0 <= bullet.y < field_h:
            moved.append(bullet)
    return moved


def update_enemies(state: GameState, field_w: int, field_h: int) -> None:
    """Advance enemy positions and fire enemy projectiles."""
    spawned_enemy_bullets: list[Bullet] = []

    for enemy in state.enemies:
        spec = ENEMY_SPECS[enemy.kind]
        if enemy.kind == "zigzag":
            enemy.y += spec.speed
            enemy.phase += 1
            if enemy.phase % 3 == 0:
                enemy.x += enemy.direction
                if enemy.x <= 0 or enemy.x >= field_w - enemy.width:
                    enemy.direction *= -1
                    enemy.x = max(0, min(field_w - enemy.width, enemy.x))
        elif enemy.kind == "turret":
            enemy.y += spec.speed
            enemy.fire_timer -= 1
            if enemy.fire_timer <= 0 and enemy.y > 2:
                spawned_enemy_bullets.append(
                    Bullet(x=enemy.x + enemy.width // 2, y=enemy.y + 1, dy=1.0, friendly=False)
                )
                enemy.fire_timer = 30
        elif enemy.kind == "carrier":
            target_y = max(3, field_h // 3)
            if enemy.y < target_y:
                enemy.y += spec.speed
            enemy.phase += 1
            if enemy.phase % 2 == 0:
                enemy.x += enemy.direction
                if enemy.x <= 0 or enemy.x >= field_w - enemy.width:
                    enemy.direction *= -1
                    enemy.x = max(0, min(field_w - enemy.width, enemy.x))
            enemy.fire_timer -= 1
            if enemy.fire_timer <= 0:
                for delta in (-1, 0, 1):
                    shot_x = max(0, min(field_w - 1, int(round(enemy.x + enemy.width // 2)) + delta))
                    spawned_enemy_bullets.append(
                        Bullet(x=float(shot_x), y=enemy.y + 1, dy=1.0, friendly=False)
                    )
                enemy.fire_timer = 18
        else:
            enemy.y += spec.speed

    state.enemies = [enemy for enemy in state.enemies if enemy.y < field_h]
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
    if state.fire_hold_frames > 0:
        state.fire_hold_frames -= 1
    if state.player_invuln > 0:
        state.player_invuln -= 1
    if state.banner_timer > 0:
        state.banner_timer -= 1

    spawn_for_mode(state, field_w, field_h, rng)
    update_enemies(state, field_w, field_h)
    state.bullets = _move_bullets(state.bullets, field_h)
    state.enemy_bullets = _move_bullets(state.enemy_bullets, field_h)
    resolve_collisions(state, field_w, field_h)


def handle_playing_keys(state: GameState, keys: list[int], field_w: int, field_h: int) -> None:
    """Apply gameplay controls after the current input queue has been read."""
    if any(key in PAUSE_KEYS for key in keys):
        state.paused = not state.paused
        return

    if state.paused:
        return

    if any(key in MOVE_LEFT_KEYS for key in keys):
        state.player_x = clamp_player_x(state.player_x, -PLAYER_STRAFE_STEP, field_w)
    if any(key in MOVE_RIGHT_KEYS for key in keys):
        state.player_x = clamp_player_x(state.player_x, PLAYER_STRAFE_STEP, field_w)
    if any(key in AUTOFIRE_TOGGLE_KEYS for key in keys):
        toggle_autofire(state)
    if any(key in FIRE_KEYS for key in keys):
        state.fire_hold_frames = FIRE_HOLD_FRAMES
    if state.shot_cooldown == 0 and (state.autofire_enabled or state.fire_hold_frames > 0):
        fire_player_shot(state, field_h)


def handle_input(stdscr, state: GameState, field_w: int, field_h: int) -> str | None:
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
            start_game(state, field_w)
        return None

    if state.screen in {"gameover", "cleared"}:
        if any(key in RESTART_KEYS for key in keys):
            state.screen = "title"
            state.paused = False
        return None

    handle_playing_keys(state, keys, field_w, field_h)
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
    subtitle = "Nokia-inspired vertical shooter"
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
        blurb = "Fly a larger starship through three tighter lanes, with room to dodge and faster side-to-side control."
    else:
        blurb = "Survive the compact lane layout as the descending waves get denser and faster."
    safe_addstr(stdscr, y, max(0, (width - len(blurb)) // 2), blurb, dim_attr)
    y += 2

    gameplay_hint = "In game: A/D or ←/→ move   HOLD SPACE fire   F autofire   P pause"
    safe_addstr(stdscr, y, max(0, (width - len(gameplay_hint)) // 2), gameplay_hint, dim_attr)

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
    hud_parts = [
        f"Score {state.score}",
        f"Lives {state.lives}",
        f"Mode {mode_text}",
        phase_text,
        f"HI {hi_score}",
    ]
    if state.autofire_enabled:
        hud_parts.insert(3, "AUTO")
    hud_line = "  |  ".join(hud_parts)

    _draw_border(stdscr, ox, oy, field_w, field_h, border_attr)
    safe_addstr(stdscr, oy - 1, max(0, (width - len(hud_line)) // 2), hud_line, hud_attr)

    ship_y = player_row(field_h)
    if state.player_invuln == 0 or state.player_invuln % 4 < 2:
        safe_addstr(stdscr, oy + 1 + ship_y, ox + 1 + state.player_x, PLAYER_GLYPH, player_attr)

    for bullet in state.bullets:
        safe_addstr(
            stdscr,
            oy + 1 + int(round(bullet.y)),
            ox + 1 + int(round(bullet.x)),
            "|",
            bullet_attr,
        )
    for bullet in state.enemy_bullets:
        safe_addstr(
            stdscr,
            oy + 1 + int(round(bullet.y)),
            ox + 1 + int(round(bullet.x)),
            "!",
            enemy_attr,
        )

    for enemy in state.enemies:
        attr = boss_attr if enemy.kind == "carrier" else enemy_attr
        safe_addstr(
            stdscr,
            oy + 1 + int(round(enemy.y)),
            ox + 1 + int(round(enemy.x)),
            ENEMY_SPECS[enemy.kind].glyph,
            attr,
        )

    if state.banner_timer > 0 and state.banner_text:
        safe_addstr(stdscr, oy + field_h + 2, max(0, (width - len(state.banner_text)) // 2), state.banner_text, hud_attr)


def render_overlay(stdscr, title: str, hint: str, has_color: bool) -> None:
    height, width = stdscr.getmaxyx()
    attr = curses.color_pair(2) | curses.A_BOLD if has_color else curses.A_BOLD
    safe_addstr(stdscr, height // 2 - 1, max(0, (width - len(title)) // 2), title, attr)
    safe_addstr(stdscr, height // 2 + 1, max(0, (width - len(hint)) // 2), hint, curses.A_DIM)


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
    stdscr.keypad(True)
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

        if height < MIN_HEIGHT or width < MIN_WIDTH:
            render(stdscr, state, has_color)
            action = handle_input(stdscr, state, 1, 1)
            if action == "quit":
                break
            curses.napms(50)
            continue

        _, _, field_w, field_h = compute_playfield(height, width)
        if state.screen == "title" and state.player_x == 0:
            state.player_x = max(0, field_w // 2 - PLAYER_WIDTH // 2)

        action = handle_input(stdscr, state, field_w, field_h)
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
