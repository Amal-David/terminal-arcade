"""Nokia-style Snake — terminal game built with curses."""

from __future__ import annotations

import curses
import random
import time
from dataclasses import dataclass, field

from .storage import load_high_score, save_high_score

# ── Constants ────────────────────────────────────────────────────────────────

FPS = 20
FRAME_TIME = 1.0 / FPS

CELL_W = 2  # each cell is 2 chars wide for square aspect ratio

# Grid fills a bit over two thirds of the terminal, computed at runtime
GRID_FILL = 0.68

INITIAL_SPEED = 6.0  # moves per second
MAX_SPEED = 14.0
SPEED_STEP = 0.8
SPEED_FOOD_INTERVAL = 5  # speed up every N food items

FOOD_SCORE = 10
BONUS_SCORE = 30
BONUS_SPAWN_CHANCE = 0.15
BONUS_LIFETIME = 120  # frames (~6 seconds)

SCORE_FLASH_FRAMES = 8

MIN_WIDTH = 50
MIN_HEIGHT = 20

# Direction vectors
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

OPPOSITES = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

# Snake characters (head shows direction with a small connector to the body)
HEAD_CHARS = {
    UP: "▀▀",
    DOWN: "▄▄",
    LEFT: "◀█",
    RIGHT: "█▶",
}
BODY_CHAR = "██"
FOOD_CHAR = "◆◆"
BONUS_CHAR = "★★"

# ── Title Art ────────────────────────────────────────────────────────────────

TITLE_ART = [
    "  ███████╗███╗   ██╗ █████╗ ██╗  ██╗███████╗",
    "  ██╔════╝████╗  ██║██╔══██╗██║ ██╔╝██╔════╝",
    "  ███████╗██╔██╗ ██║███████║█████╔╝ █████╗  ",
    "  ╚════██║██║╚██╗██║██╔══██║██╔═██╗ ██╔══╝  ",
    "  ███████║██║ ╚████║██║  ██║██║  ██╗███████╗",
    "  ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝",
]

SNAKE_ART = [
    "      ██████████████████████████████████████████████████►► ◆◆",
    "      ██",
    "      ████████████████████████████████►►",
]


# ── Grid sizing ──────────────────────────────────────────────────────────────

def compute_grid_size(term_h: int, term_w: int) -> tuple[int, int]:
    """Compute grid dimensions to fill ~80% of the terminal."""
    # Reserve 3 rows for HUD (top) and 1 for bottom margin
    available_h = term_h - 4
    # Reserve 2 cols for border chars
    available_w = term_w - 2

    grid_h = max(10, int(available_h * GRID_FILL))
    grid_w = max(15, int((available_w * GRID_FILL) / CELL_W))

    return grid_w, grid_h


# ── State ────────────────────────────────────────────────────────────────────

@dataclass
class GameState:
    grid_w: int = 30
    grid_h: int = 20
    snake: list[tuple[int, int]] = field(default_factory=list)
    direction: tuple[int, int] = field(default_factory=lambda: RIGHT)
    next_direction: tuple[int, int] = field(default_factory=lambda: RIGHT)
    food: tuple[int, int] = field(default_factory=lambda: (0, 0))
    bonus_food: tuple[int, int] | None = None
    bonus_timer: int = 0
    score: int = 0
    high_score: int = 0
    speed: float = INITIAL_SPEED
    started: bool = False
    is_dead: bool = False
    is_paused: bool = False
    frame_count: int = 0
    move_timer: float = 0.0
    food_eaten: int = 0
    score_flash_timer: int = 0
    new_high_score: bool = False
    high_score_dirty: bool = False
    running: bool = True
    death_anim_frame: int = 0


def new_game(high_score: int, grid_w: int = 30, grid_h: int = 20) -> GameState:
    state = GameState()
    state.grid_w = grid_w
    state.grid_h = grid_h
    state.high_score = high_score
    # Start snake in the center
    cx, cy = grid_w // 2, grid_h // 2
    state.snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
    state.food = spawn_food(state)
    return state


# ── Game Logic ───────────────────────────────────────────────────────────────

def spawn_food(state: GameState) -> tuple[int, int]:
    occupied = set(state.snake)
    if state.bonus_food:
        occupied.add(state.bonus_food)
    while True:
        pos = (random.randint(0, state.grid_w - 1), random.randint(0, state.grid_h - 1))
        if pos not in occupied:
            return pos


def spawn_bonus(state: GameState) -> tuple[int, int] | None:
    if random.random() < BONUS_SPAWN_CHANCE:
        occupied = set(state.snake)
        occupied.add(state.food)
        for _ in range(50):
            pos = (random.randint(0, state.grid_w - 1), random.randint(0, state.grid_h - 1))
            if pos not in occupied:
                return pos
    return None


def move_snake(state: GameState) -> None:
    state.direction = state.next_direction
    hx, hy = state.snake[0]
    dx, dy = state.direction
    new_head = (hx + dx, hy + dy)

    # Wall collision ends the run.
    if not (0 <= new_head[0] < state.grid_w and 0 <= new_head[1] < state.grid_h):
        state.is_dead = True
        return

    # Self-collision
    if new_head in set(state.snake):
        state.is_dead = True
        return

    state.snake.insert(0, new_head)

    ate_food = False
    ate_bonus = False

    if new_head == state.food:
        ate_food = True
        state.score += FOOD_SCORE
        state.food_eaten += 1
        state.score_flash_timer = SCORE_FLASH_FRAMES
        state.food = spawn_food(state)

        # Speed progression
        if state.food_eaten % SPEED_FOOD_INTERVAL == 0 and state.speed < MAX_SPEED:
            state.speed = min(MAX_SPEED, state.speed + SPEED_STEP)

        # Maybe spawn bonus
        if state.bonus_food is None:
            state.bonus_food = spawn_bonus(state)
            if state.bonus_food:
                state.bonus_timer = BONUS_LIFETIME

    elif state.bonus_food and new_head == state.bonus_food:
        ate_bonus = True
        state.score += BONUS_SCORE
        state.score_flash_timer = SCORE_FLASH_FRAMES
        state.bonus_food = None
        state.bonus_timer = 0

    if not ate_food and not ate_bonus:
        state.snake.pop()

    # Update high score
    if state.score > state.high_score:
        state.high_score = state.score
        state.new_high_score = True
        state.high_score_dirty = True


def update(state: GameState) -> None:
    if not state.started or state.is_dead or state.is_paused:
        return

    state.frame_count += 1

    # Bonus food timer
    if state.bonus_food:
        state.bonus_timer -= 1
        if state.bonus_timer <= 0:
            state.bonus_food = None

    # Score flash timer
    if state.score_flash_timer > 0:
        state.score_flash_timer -= 1

    # Move snake based on speed
    state.move_timer += state.speed / FPS
    while state.move_timer >= 1.0:
        state.move_timer -= 1.0
        move_snake(state)
        if state.is_dead:
            break

    if state.is_dead:
        state.death_anim_frame = 0


# ── Input ────────────────────────────────────────────────────────────────────

def handle_input(stdscr, state: GameState) -> str | None:
    keys = []
    while True:
        key = stdscr.getch()
        if key == -1:
            break
        keys.append(key)

    has_quit = False
    has_start = False
    has_pause = False
    new_dir = None

    for key in keys:
        if key in (ord("q"), ord("Q"), 27):  # Q or Esc
            has_quit = True
        elif key in (ord(" "), curses.KEY_ENTER, 10, 13):
            has_start = True
        elif key in (ord("p"), ord("P")):
            has_pause = True
        elif key in (curses.KEY_UP, ord("w"), ord("W")):
            new_dir = UP
        elif key in (curses.KEY_DOWN, ord("s"), ord("S")):
            new_dir = DOWN
        elif key in (curses.KEY_LEFT, ord("a"), ord("A")):
            new_dir = LEFT
        elif key in (curses.KEY_RIGHT, ord("d"), ord("D")):
            new_dir = RIGHT

    if has_quit:
        return "quit"

    if not state.started:
        if has_start:
            state.started = True
        return None

    if state.is_dead:
        state.death_anim_frame += 1
        if has_start and state.death_anim_frame > 10:
            return "restart"
        return None

    if has_pause:
        state.is_paused = not state.is_paused
        return None

    if state.is_paused:
        return None

    # Direction change — no 180° reversals
    if new_dir and new_dir != OPPOSITES.get(state.direction):
        state.next_direction = new_dir

    return None


# ── Rendering ────────────────────────────────────────────────────────────────

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
    curses.init_pair(1, curses.COLOR_GREEN, -1)   # snake
    curses.init_pair(2, curses.COLOR_RED, -1)      # food
    curses.init_pair(3, curses.COLOR_YELLOW, -1)   # bonus / title
    curses.init_pair(4, curses.COLOR_WHITE, -1)    # border
    curses.init_pair(5, curses.COLOR_CYAN, -1)     # UI text
    curses.init_pair(6, curses.COLOR_RED, -1)      # game over
    return True


def render_title(stdscr, state: GameState, height: int, width: int, has_color: bool) -> None:
    title_attr = curses.color_pair(1) | curses.A_BOLD if has_color else curses.A_BOLD
    dim_attr = curses.A_DIM
    art_attr = curses.color_pair(3) | curses.A_BOLD if has_color else curses.A_BOLD

    # Center vertically
    total_lines = len(TITLE_ART) + 1 + len(SNAKE_ART) + 8
    y = max(1, (height - total_lines) // 2)

    for line in TITLE_ART:
        safe_addstr(stdscr, y, max(0, (width - len(line)) // 2), line, title_attr)
        y += 1

    y += 1
    for line in SNAKE_ART:
        safe_addstr(stdscr, y, max(0, (width - len(line)) // 2), line, art_attr)
        y += 1

    y += 2
    sub = "classic nokia snake for your terminal"
    safe_addstr(stdscr, y, max(0, (width - len(sub)) // 2), sub, dim_attr)

    y += 2
    if state.high_score > 0:
        hi = f"High Score: {state.high_score}"
        safe_addstr(stdscr, y, max(0, (width - len(hi)) // 2), hi, art_attr)
        y += 1

    y += 1
    start = "Press SPACE or ENTER to play"
    if (state.frame_count // 10) % 2:
        safe_addstr(stdscr, y, max(0, (width - len(start)) // 2), start, curses.A_BOLD)

    controls = "Arrow keys / WASD move   P pause   Q quit"
    safe_addstr(stdscr, height - 2, max(0, (width - len(controls)) // 2), controls, dim_attr)


def render_game(stdscr, state: GameState, height: int, width: int, has_color: bool) -> None:
    snake_attr = curses.color_pair(1) | curses.A_BOLD if has_color else curses.A_BOLD
    food_attr = curses.color_pair(2) | curses.A_BOLD if has_color else curses.A_BOLD
    bonus_attr = curses.color_pair(3) | curses.A_BOLD if has_color else curses.A_BOLD
    border_attr = curses.color_pair(4) if has_color else curses.A_DIM
    dead_attr = curses.color_pair(6) | curses.A_BOLD if has_color else curses.A_BOLD

    gw = state.grid_w
    gh = state.grid_h

    # Grid pixel dimensions (border included)
    grid_pixel_w = gw * CELL_W + 2
    grid_pixel_h = gh + 2

    # Center the grid in the terminal
    ox = max(0, (width - grid_pixel_w) // 2)
    oy = max(2, (height - grid_pixel_h) // 2)

    # ── HUD row (above the grid) ──
    hud_y = oy - 1
    score_text = f"Score: {state.score}"
    length_text = f"Length: {len(state.snake)}"
    speed_text = f"Speed: {state.speed:.0f}"
    hi_text = f"HI {state.high_score}" if state.high_score > 0 else ""

    if state.score_flash_timer > 0 and state.score_flash_timer % 2 == 0:
        score_attr = curses.A_NORMAL
    else:
        score_attr = curses.color_pair(3) | curses.A_BOLD if has_color else curses.A_BOLD

    safe_addstr(stdscr, hud_y, ox + 1, score_text, score_attr)
    safe_addstr(stdscr, hud_y, ox + (grid_pixel_w - len(length_text)) // 2, length_text, curses.A_DIM)
    right_text = f"{hi_text}  {speed_text}" if hi_text else speed_text
    safe_addstr(stdscr, hud_y, ox + grid_pixel_w - len(right_text) - 1, right_text, curses.A_DIM)

    # ── Border ──
    safe_addstr(stdscr, oy, ox, "╔" + "═" * (gw * CELL_W) + "╗", border_attr)
    for row in range(gh):
        safe_addstr(stdscr, oy + 1 + row, ox, "║", border_attr)
        safe_addstr(stdscr, oy + 1 + row, ox + 1 + gw * CELL_W, "║", border_attr)
    safe_addstr(stdscr, oy + gh + 1, ox, "╚" + "═" * (gw * CELL_W) + "╝", border_attr)

    # ── Grid contents ──
    snake_set = set(state.snake)
    head = state.snake[0] if state.snake else None

    for row in range(gh):
        for col in range(gw):
            pos = (col, row)
            # Skip empty cells for performance
            if pos not in snake_set and pos != state.food and pos != state.bonus_food:
                continue

            cx = ox + 1 + col * CELL_W
            cy = oy + 1 + row

            if pos == head:
                char = HEAD_CHARS.get(state.direction, "██")
                attr = dead_attr if state.is_dead else snake_attr
                safe_addstr(stdscr, cy, cx, char, attr)
            elif pos in snake_set:
                attr = dead_attr if state.is_dead else snake_attr
                safe_addstr(stdscr, cy, cx, BODY_CHAR, attr)
            elif pos == state.food:
                safe_addstr(stdscr, cy, cx, FOOD_CHAR, food_attr)
            elif pos == state.bonus_food:
                if state.bonus_timer > 30 or state.frame_count % 4 < 3:
                    safe_addstr(stdscr, cy, cx, BONUS_CHAR, bonus_attr)


def render_pause(stdscr, height: int, width: int, has_color: bool) -> None:
    attr = curses.color_pair(3) | curses.A_BOLD if has_color else curses.A_BOLD
    text = "P A U S E D"
    hint = "Press P to resume"
    safe_addstr(stdscr, height // 2 - 1, max(0, (width - len(text)) // 2), text, attr)
    safe_addstr(stdscr, height // 2 + 1, max(0, (width - len(hint)) // 2), hint, curses.A_DIM)


def render_game_over(stdscr, state: GameState, height: int, width: int, has_color: bool) -> None:
    attr = curses.color_pair(6) | curses.A_BOLD if has_color else curses.A_BOLD

    title = "G A M E   O V E R"
    score = f"Score: {state.score}"
    best = f"Best:  {state.high_score}"
    restart = "Press SPACE or ENTER to retry"

    cy = height // 2 - 2
    safe_addstr(stdscr, cy, max(0, (width - len(title)) // 2), title, attr)
    safe_addstr(stdscr, cy + 2, max(0, (width - len(score)) // 2), score, curses.A_BOLD)
    safe_addstr(stdscr, cy + 3, max(0, (width - len(best)) // 2), best, curses.A_BOLD)

    if state.new_high_score:
        nb = "*** NEW BEST ***"
        safe_addstr(stdscr, cy + 4, max(0, (width - len(nb)) // 2), nb, curses.A_DIM)

    if (state.death_anim_frame // 10) % 2 == 0:
        safe_addstr(stdscr, cy + 6, max(0, (width - len(restart)) // 2), restart, curses.A_DIM)


def render(stdscr, state: GameState, has_color: bool) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()

    if height < MIN_HEIGHT or width < MIN_WIDTH:
        msg = f"Terminal too small ({width}x{height}). Need {MIN_WIDTH}x{MIN_HEIGHT}."
        safe_addstr(stdscr, height // 2, max(0, (width - len(msg)) // 2), msg, curses.A_BOLD)
        stdscr.refresh()
        return

    if not state.started:
        render_title(stdscr, state, height, width, has_color)
    else:
        render_game(stdscr, state, height, width, has_color)
        if state.is_paused:
            render_pause(stdscr, height, width, has_color)
        elif state.is_dead:
            render_game_over(stdscr, state, height, width, has_color)

    stdscr.refresh()


# ── Main Loop ────────────────────────────────────────────────────────────────

def main(stdscr) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)
    has_color = init_colors()

    high_score = load_high_score()
    height, width = stdscr.getmaxyx()
    grid_w, grid_h = compute_grid_size(height, width)
    state = new_game(high_score, grid_w, grid_h)

    while state.running:
        frame_start = time.monotonic()

        # Tick frame counter for title screen animation
        if not state.started:
            state.frame_count += 1

        action = handle_input(stdscr, state)

        if action == "quit":
            state.running = False
            break
        elif action == "restart":
            if state.high_score_dirty:
                save_high_score(state.high_score)
            # Recompute grid in case terminal was resized
            height, width = stdscr.getmaxyx()
            grid_w, grid_h = compute_grid_size(height, width)
            state = new_game(state.high_score, grid_w, grid_h)
            state.started = True
            continue

        update(state)
        render(stdscr, state, has_color)

        elapsed = time.monotonic() - frame_start
        sleep_ms = max(1, int((FRAME_TIME - elapsed) * 1000))
        curses.napms(sleep_ms)

    if state.high_score_dirty:
        save_high_score(state.high_score)


def run() -> None:
    curses.wrapper(main)


if __name__ == "__main__":
    run()
