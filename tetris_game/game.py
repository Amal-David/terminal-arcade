"""Classic single-player Tetris for the terminal arcade."""

from __future__ import annotations

import curses
import random
import time
from dataclasses import dataclass, field

from .storage import load_high_score, save_high_score


FPS = 30
FRAME_TIME = 1.0 / FPS
MIN_WIDTH = 72
MIN_HEIGHT = 26

BOARD_W = 10
BOARD_H = 20
PREVIEW_W = 6
PREVIEW_H = 4

MOVE_LEFT_KEYS = {curses.KEY_LEFT, ord("a"), ord("A")}
MOVE_RIGHT_KEYS = {curses.KEY_RIGHT, ord("d"), ord("D")}
SOFT_DROP_KEYS = {curses.KEY_DOWN, ord("s"), ord("S")}
HARD_DROP_KEYS = {ord(" ")}
ROTATE_CW_KEYS = {curses.KEY_UP, ord("x"), ord("X")}
ROTATE_CCW_KEYS = {ord("z"), ord("Z")}
PAUSE_KEYS = {ord("p"), ord("P")}
QUIT_KEYS = {ord("q"), ord("Q"), 27}
START_KEYS = {ord(" "), curses.KEY_ENTER, 10, 13}

PIECE_COLORS = {
    "I": 1,
    "O": 2,
    "T": 3,
    "S": 4,
    "Z": 5,
    "J": 6,
    "L": 7,
}

PIECE_NAMES = {
    "I": "I-Bar",
    "O": "Square",
    "T": "Tee",
    "S": "Snake",
    "Z": "Zigzag",
    "J": "J-Hook",
    "L": "L-Hook",
}

PIECE_ORDER = ("I", "O", "T", "S", "Z", "J", "L")

TETROMINOES = {
    "I": (
        ((0, 1), (1, 1), (2, 1), (3, 1)),
        ((2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 2), (1, 2), (2, 2), (3, 2)),
        ((1, 0), (1, 1), (1, 2), (1, 3)),
    ),
    "O": (
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
    ),
    "T": (
        ((1, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (2, 1), (1, 2)),
        ((0, 1), (1, 1), (2, 1), (1, 2)),
        ((1, 0), (0, 1), (1, 1), (1, 2)),
    ),
    "S": (
        ((1, 0), (2, 0), (0, 1), (1, 1)),
        ((1, 0), (1, 1), (2, 1), (2, 2)),
        ((1, 1), (2, 1), (0, 2), (1, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    "Z": (
        ((0, 0), (1, 0), (1, 1), (2, 1)),
        ((2, 0), (1, 1), (2, 1), (1, 2)),
        ((0, 1), (1, 1), (1, 2), (2, 2)),
        ((1, 0), (0, 1), (1, 1), (0, 2)),
    ),
    "J": (
        ((0, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (1, 2)),
        ((0, 1), (1, 1), (2, 1), (2, 2)),
        ((1, 0), (1, 1), (0, 2), (1, 2)),
    ),
    "L": (
        ((2, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (1, 2), (2, 2)),
        ((0, 1), (1, 1), (2, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1), (1, 2)),
    ),
}

JLSTZ_KICKS = {
    (0, 1): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
    (1, 0): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
    (1, 2): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
    (2, 1): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
    (2, 3): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
    (3, 2): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
    (3, 0): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
    (0, 3): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
}

I_KICKS = {
    (0, 1): ((0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)),
    (1, 0): ((0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)),
    (1, 2): ((0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)),
    (2, 1): ((0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)),
    (2, 3): ((0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)),
    (3, 2): ((0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)),
    (3, 0): ((0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)),
    (0, 3): ((0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)),
}

LINE_SCORES = {
    1: 100,
    2: 300,
    3: 500,
    4: 800,
}

TITLE_ART = [
    " ████████╗███████╗████████╗██████╗ ██╗███████╗",
    " ╚══██╔══╝██╔════╝╚══██╔══╝██╔══██╗██║██╔════╝",
    "    ██║   █████╗     ██║   ██████╔╝██║███████╗",
    "    ██║   ██╔══╝     ██║   ██╔══██╗██║╚════██║",
    "    ██║   ███████╗   ██║   ██║  ██║██║███████║",
    "    ╚═╝   ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚══════╝",
]


@dataclass
class Piece:
    kind: str
    rotation: int = 0
    x: int = 3
    y: int = 0


@dataclass
class GameState:
    board: list[list[str | None]] = field(default_factory=list)
    current: Piece | None = None
    next_kind: str = "I"
    bag: list[str] = field(default_factory=list)
    score: int = 0
    lines: int = 0
    level: int = 1
    high_score: int = 0
    started: bool = False
    is_dead: bool = False
    is_paused: bool = False
    running: bool = True
    drop_progress: float = 0.0
    frame_count: int = 0
    game_over_timer: int = 0
    high_score_dirty: bool = False
    new_high_score: bool = False


def empty_board() -> list[list[str | None]]:
    return [[None for _ in range(BOARD_W)] for _ in range(BOARD_H)]


def gravity_for_level(level: int) -> float:
    return min(2.6, 0.04 + (level - 1) * 0.03)


def make_bag(rng: random.Random) -> list[str]:
    bag = list(PIECE_ORDER)
    rng.shuffle(bag)
    return bag


def cells_for(piece: Piece) -> tuple[tuple[int, int], ...]:
    return tuple((piece.x + dx, piece.y + dy) for dx, dy in TETROMINOES[piece.kind][piece.rotation])


def can_place(board: list[list[str | None]], piece: Piece) -> bool:
    for x, y in cells_for(piece):
        if x < 0 or x >= BOARD_W or y >= BOARD_H:
            return False
        if y >= 0 and board[y][x] is not None:
            return False
    return True


def fill_queue(state: GameState, rng: random.Random) -> None:
    if not state.bag:
        state.bag = make_bag(rng)


def pop_next_kind(state: GameState, rng: random.Random) -> str:
    fill_queue(state, rng)
    kind = state.bag.pop(0)
    fill_queue(state, rng)
    return kind


def spawn_piece(state: GameState, rng: random.Random) -> bool:
    kind = state.next_kind
    state.current = Piece(kind=kind, rotation=0, x=3, y=-1)
    state.next_kind = pop_next_kind(state, rng)
    return can_place(state.board, state.current)


def start_game(state: GameState, rng: random.Random) -> None:
    state.board = empty_board()
    state.bag = []
    state.score = 0
    state.lines = 0
    state.level = 1
    state.started = True
    state.is_dead = False
    state.is_paused = False
    state.drop_progress = 0.0
    state.frame_count = 0
    state.game_over_timer = 0
    state.new_high_score = False
    state.next_kind = pop_next_kind(state, rng)
    spawn_piece(state, rng)


def try_move(state: GameState, dx: int, dy: int) -> bool:
    if state.current is None:
        return False
    moved = Piece(state.current.kind, state.current.rotation, state.current.x + dx, state.current.y + dy)
    if can_place(state.board, moved):
        state.current = moved
        return True
    return False


def kick_tests(kind: str, from_rotation: int, to_rotation: int) -> tuple[tuple[int, int], ...]:
    if kind == "O":
        return ((0, 0),)
    if kind == "I":
        return I_KICKS[(from_rotation, to_rotation)]
    return JLSTZ_KICKS[(from_rotation, to_rotation)]


def try_rotate(state: GameState, direction: int) -> bool:
    if state.current is None:
        return False
    old = state.current
    new_rotation = (old.rotation + direction) % 4
    for dx, dy in kick_tests(old.kind, old.rotation, new_rotation):
        rotated = Piece(old.kind, new_rotation, old.x + dx, old.y + dy)
        if can_place(state.board, rotated):
            state.current = rotated
            return True
    return False


def lock_piece(state: GameState) -> int:
    if state.current is None:
        return 0
    for x, y in cells_for(state.current):
        if 0 <= y < BOARD_H:
            state.board[y][x] = state.current.kind
    cleared = clear_lines(state)
    state.current = None
    return cleared


def clear_lines(state: GameState) -> int:
    kept = [row for row in state.board if any(cell is None for cell in row)]
    cleared = BOARD_H - len(kept)
    if cleared:
        state.board = [[None for _ in range(BOARD_W)] for _ in range(cleared)] + kept
        state.lines += cleared
        state.level = state.lines // 10 + 1
        state.score += LINE_SCORES[cleared] * state.level
        update_high_score(state)
    return cleared


def update_high_score(state: GameState) -> None:
    if state.score > state.high_score:
        state.high_score = state.score
        state.high_score_dirty = True
        state.new_high_score = True


def settle_current_piece(state: GameState, rng: random.Random) -> None:
    lock_piece(state)
    if not spawn_piece(state, rng):
        state.is_dead = True
        state.game_over_timer = 0


def soft_drop(state: GameState, rng: random.Random) -> bool:
    if try_move(state, 0, 1):
        state.score += 1
        update_high_score(state)
        return True
    settle_current_piece(state, rng)
    return False


def hard_drop_distance(state: GameState) -> int:
    if state.current is None:
        return 0
    distance = 0
    probe = Piece(state.current.kind, state.current.rotation, state.current.x, state.current.y)
    while can_place(state.board, Piece(probe.kind, probe.rotation, probe.x, probe.y + 1)):
        probe.y += 1
        distance += 1
    return distance


def hard_drop(state: GameState, rng: random.Random) -> int:
    if state.current is None:
        return 0
    distance = hard_drop_distance(state)
    state.current = Piece(state.current.kind, state.current.rotation, state.current.x, state.current.y + distance)
    state.score += distance * 2
    update_high_score(state)
    settle_current_piece(state, rng)
    return distance


def board_with_current(state: GameState) -> list[list[str | None]]:
    board = [row[:] for row in state.board]
    if state.current is not None:
        for x, y in cells_for(state.current):
            if 0 <= y < BOARD_H:
                board[y][x] = state.current.kind
    return board


def handle_input(stdscr, state: GameState, rng: random.Random) -> str | None:
    keys: list[int] = []
    while True:
        key = stdscr.getch()
        if key == -1:
            break
        keys.append(key)

    if any(key in QUIT_KEYS for key in keys):
        return "quit"

    if not state.started:
        if any(key in START_KEYS for key in keys):
            start_game(state, rng)
        return None

    if state.is_dead:
        state.game_over_timer += 1
        if state.game_over_timer > 8 and any(key in START_KEYS for key in keys):
            start_game(state, rng)
        return None

    if any(key in PAUSE_KEYS for key in keys):
        state.is_paused = not state.is_paused
        return None

    if state.is_paused:
        return None

    if any(key in MOVE_LEFT_KEYS for key in keys):
        try_move(state, -1, 0)
    if any(key in MOVE_RIGHT_KEYS for key in keys):
        try_move(state, 1, 0)
    if any(key in ROTATE_CW_KEYS for key in keys):
        try_rotate(state, 1)
    if any(key in ROTATE_CCW_KEYS for key in keys):
        try_rotate(state, -1)
    if any(key in SOFT_DROP_KEYS for key in keys):
        soft_drop(state, rng)
        state.drop_progress = 0.0
    if any(key in HARD_DROP_KEYS for key in keys):
        hard_drop(state, rng)
        state.drop_progress = 0.0
    return None


def update(state: GameState, rng: random.Random) -> None:
    if not state.started or state.is_dead or state.is_paused:
        return

    state.frame_count += 1
    state.drop_progress += gravity_for_level(state.level)
    while state.drop_progress >= 1.0 and not state.is_dead:
        state.drop_progress -= 1.0
        if not try_move(state, 0, 1):
            settle_current_piece(state, rng)
            break


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
    curses.init_pair(3, curses.COLOR_MAGENTA, -1)
    curses.init_pair(4, curses.COLOR_GREEN, -1)
    curses.init_pair(5, curses.COLOR_RED, -1)
    curses.init_pair(6, curses.COLOR_BLUE, -1)
    curses.init_pair(7, curses.COLOR_WHITE, -1)
    curses.init_pair(8, curses.COLOR_WHITE, -1)
    return True


def board_origin(height: int, width: int) -> tuple[int, int]:
    board_pixel_w = BOARD_W * 2 + 2
    board_pixel_h = BOARD_H + 2
    ox = max(2, (width - board_pixel_w - 20) // 2)
    oy = max(2, (height - board_pixel_h) // 2)
    return ox, oy


def render_title(stdscr, state: GameState, height: int, width: int, has_color: bool) -> None:
    title_attr = curses.color_pair(2) | curses.A_BOLD if has_color else curses.A_BOLD
    accent_attr = curses.color_pair(1) | curses.A_BOLD if has_color else curses.A_BOLD
    y = max(1, (height - 18) // 2)
    for line in TITLE_ART:
        safe_addstr(stdscr, y, max(0, (width - len(line)) // 2), line, title_attr)
        y += 1
    subtitle = "classic endless block stacking"
    safe_addstr(stdscr, y + 1, max(0, (width - len(subtitle)) // 2), subtitle, curses.A_DIM)
    hi = f"High Score: {state.high_score}"
    safe_addstr(stdscr, y + 3, max(0, (width - len(hi)) // 2), hi, accent_attr)
    hint = "One next piece, no hold, standard wall kicks"
    safe_addstr(stdscr, y + 5, max(0, (width - len(hint)) // 2), hint, curses.A_DIM)
    start = "Press SPACE or ENTER to play"
    if (state.frame_count // 10) % 2 == 0:
        safe_addstr(stdscr, y + 8, max(0, (width - len(start)) // 2), start, curses.A_BOLD)
    controls = "←/A left  →/D right  ↓/S drop  SPACE hard drop  X/↑ cw  Z ccw  P pause  Q quit"
    safe_addstr(stdscr, height - 2, max(0, (width - len(controls)) // 2), controls, curses.A_DIM)


def render_board(stdscr, state: GameState, height: int, width: int, has_color: bool) -> None:
    ox, oy = board_origin(height, width)
    border_attr = curses.color_pair(8) if has_color else curses.A_DIM
    board = board_with_current(state)

    safe_addstr(stdscr, oy, ox, "╔" + "═" * (BOARD_W * 2) + "╗", border_attr)
    for row in range(BOARD_H):
        safe_addstr(stdscr, oy + 1 + row, ox, "║", border_attr)
        safe_addstr(stdscr, oy + 1 + row, ox + BOARD_W * 2 + 1, "║", border_attr)
    safe_addstr(stdscr, oy + BOARD_H + 1, ox, "╚" + "═" * (BOARD_W * 2) + "╝", border_attr)

    for row, line in enumerate(board):
        for col, cell in enumerate(line):
            if cell is None:
                continue
            attr = curses.color_pair(PIECE_COLORS[cell]) | curses.A_BOLD if has_color else curses.A_BOLD
            safe_addstr(stdscr, oy + 1 + row, ox + 1 + col * 2, "██", attr)

    panel_x = ox + BOARD_W * 2 + 5
    header_attr = curses.color_pair(1) | curses.A_BOLD if has_color else curses.A_BOLD
    value_attr = curses.color_pair(4) | curses.A_BOLD if has_color else curses.A_BOLD
    safe_addstr(stdscr, oy + 1, panel_x, f"Score  {state.score}", header_attr)
    safe_addstr(stdscr, oy + 3, panel_x, f"Lines  {state.lines}", header_attr)
    safe_addstr(stdscr, oy + 5, panel_x, f"Level  {state.level}", header_attr)
    safe_addstr(stdscr, oy + 7, panel_x, f"HI     {state.high_score}", header_attr)
    safe_addstr(stdscr, oy + 10, panel_x, "Next", value_attr)
    render_preview(stdscr, state.next_kind, oy + 12, panel_x, has_color)


def render_preview(stdscr, kind: str, y: int, x: int, has_color: bool) -> None:
    cells = TETROMINOES[kind][0]
    min_x = min(cell_x for cell_x, _ in cells)
    min_y = min(cell_y for _, cell_y in cells)
    attr = curses.color_pair(PIECE_COLORS[kind]) | curses.A_BOLD if has_color else curses.A_BOLD
    for cell_x, cell_y in cells:
        draw_x = x + (cell_x - min_x) * 2
        draw_y = y + (cell_y - min_y)
        safe_addstr(stdscr, draw_y, draw_x, "██", attr)
    safe_addstr(stdscr, y + PREVIEW_H + 1, x, PIECE_NAMES[kind], curses.A_DIM)


def render_overlay(stdscr, title: str, hint: str, has_color: bool) -> None:
    height, width = stdscr.getmaxyx()
    attr = curses.color_pair(2) | curses.A_BOLD if has_color else curses.A_BOLD
    safe_addstr(stdscr, height // 2 - 1, max(0, (width - len(title)) // 2), title, attr)
    safe_addstr(stdscr, height // 2 + 1, max(0, (width - len(hint)) // 2), hint, curses.A_DIM)


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
        render_board(stdscr, state, height, width, has_color)
        if state.is_paused:
            render_overlay(stdscr, "P A U S E D", "Press P to resume", has_color)
        elif state.is_dead:
            render_overlay(stdscr, "G A M E   O V E R", "Press SPACE or ENTER to retry", has_color)

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

    state = GameState(high_score=load_high_score(), board=empty_board())
    rng = random.Random()
    fill_queue(state, rng)
    state.next_kind = pop_next_kind(state, rng)

    while state.running:
        frame_start = time.monotonic()
        if not state.started:
            state.frame_count += 1
        action = handle_input(stdscr, state, rng)
        if action == "quit":
            break
        update(state, rng)
        render(stdscr, state, has_color)
        elapsed = time.monotonic() - frame_start
        sleep_ms = max(1, int((FRAME_TIME - elapsed) * 1000))
        curses.napms(sleep_ms)

    if state.high_score_dirty:
        save_high_score(state.high_score)


def run() -> None:
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass

