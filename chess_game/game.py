"""Terminal chess cabinet with a built-in rule-based engine."""

from __future__ import annotations

import curses
from dataclasses import dataclass, field
import random
import time

from .core import (
    DIFFICULTIES,
    Difficulty,
    Position,
    game_outcome,
    generate_legal_moves,
    legal_move_from_text,
    search_best_move,
    square_name,
    undo_move,
)
from .storage import load_stats, save_stats


MIN_WIDTH = 84
MIN_HEIGHT = 28
TITLE_ART = [
    "  ██████╗██╗  ██╗███████╗███████╗███████╗",
    " ██╔════╝██║  ██║██╔════╝██╔════╝██╔════╝",
    " ██║     ███████║█████╗  ███████╗███████╗",
    " ██║     ██╔══██║██╔══╝  ╚════██║╚════██║",
    " ╚██████╗██║  ██║███████╗███████║███████║",
    "  ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝",
]
LIGHT_SQUARE = " . "
DARK_SQUARE = " : "
WHITE_TOKENS = {
    "P": "WP ",
    "N": "WN ",
    "B": "WB ",
    "R": "WR ",
    "Q": "WQ ",
    "K": "WK ",
}
BLACK_TOKENS = {
    "p": "bp ",
    "n": "bn ",
    "b": "bb ",
    "r": "br ",
    "q": "bq ",
    "k": "bk ",
}


@dataclass
class GameState:
    position: Position = field(default_factory=Position)
    difficulty_key: str = "medium"
    stats: dict[str, object] = field(default_factory=load_stats)
    screen: str = "title"
    input_buffer: str = ""
    message: str = ""
    result_text: str = ""
    running: bool = True
    thinking: bool = False
    stats_recorded: bool = False
    engine_rng: random.Random = field(default_factory=lambda: random.Random(7))
    human_color: bool = True
    last_move_time: float = 0.0


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


def init_colors() -> bool:
    if not curses.has_colors():
        return False
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_YELLOW, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_WHITE, -1)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)
    curses.init_pair(6, curses.COLOR_RED, -1)
    return True


def outcome_text(state: GameState) -> str:
    outcome = game_outcome(state.position)
    if outcome is None:
        return ""
    winner, reason = outcome
    if winner == "white":
        return f"White wins. {reason}."
    if winner == "black":
        return f"Black wins. {reason}."
    return reason


def apply_outcome(state: GameState, winner: str, reason: str) -> None:
    state.screen = "gameover"
    state.result_text = f"{reason}."
    record_result(state, winner)


def record_result(state: GameState, winner: str) -> None:
    if state.stats_recorded:
        return
    bucket = "draws"
    if winner == "black":
        bucket = "losses"
    elif winner == "white":
        bucket = "wins"
    stats_bucket = state.stats[bucket]
    stats_bucket[state.difficulty_key] = int(stats_bucket[state.difficulty_key]) + 1
    state.stats["last_difficulty"] = state.difficulty_key
    save_stats(state.stats)
    state.stats_recorded = True


def start_new_game(state: GameState) -> None:
    state.position = Position()
    state.screen = "playing"
    state.input_buffer = ""
    state.message = "Enter a move like e2e4. Type undo, new, resign, or q."
    state.result_text = ""
    state.thinking = False
    state.stats_recorded = False
    state.last_move_time = time.perf_counter()
    state.stats["last_difficulty"] = state.difficulty_key
    save_stats(state.stats)


def cycle_difficulty(state: GameState, step: int) -> None:
    keys = list(DIFFICULTIES)
    index = keys.index(state.difficulty_key)
    state.difficulty_key = keys[(index + step) % len(keys)]
    state.message = f"Difficulty set to {DIFFICULTIES[state.difficulty_key].label}."


def board_token(piece: str, row: int, col: int) -> str:
    if piece == ".":
        return LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
    if piece.isupper():
        return WHITE_TOKENS[piece]
    return BLACK_TOKENS[piece]


def render_small_terminal(stdscr, height: int, width: int) -> None:
    stdscr.erase()
    msg = f"Terminal too small ({width}x{height}). Need {MIN_WIDTH}x{MIN_HEIGHT}."
    hint = "Resize to play chess. Press Q or Esc to quit."
    safe_addstr(stdscr, height // 2 - 1, max(0, (width - len(msg)) // 2), msg, curses.A_BOLD)
    safe_addstr(stdscr, height // 2 + 1, max(0, (width - len(hint)) // 2), hint, curses.A_DIM)
    stdscr.refresh()


def render_title(stdscr, state: GameState, has_color: bool) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    title_attr = curses.color_pair(2) | curses.A_BOLD if has_color else curses.A_BOLD
    accent_attr = curses.color_pair(1) | curses.A_BOLD if has_color else curses.A_BOLD
    hint_attr = curses.color_pair(5) | curses.A_BOLD if has_color else curses.A_BOLD
    y = 1
    for line in TITLE_ART:
        safe_addstr(stdscr, y, max(0, (width - len(line)) // 2), line, title_attr)
        y += 1

    description = "Play White against the built-in engine. Choose your level and type moves in UCI form."
    safe_addstr(stdscr, y + 1, max(0, (width - len(description)) // 2), description, hint_attr)

    difficulty = DIFFICULTIES[state.difficulty_key]
    label = f"Difficulty: {difficulty.label}"
    safe_addstr(stdscr, y + 5, max(0, (width - len(label)) // 2), label, accent_attr)
    safe_addstr(stdscr, y + 7, max(0, (width - 48) // 2), "Easy: lighter search and some randomness", curses.A_DIM)
    safe_addstr(stdscr, y + 8, max(0, (width - 43) // 2), "Medium: deeper, cleaner tactical replies", curses.A_DIM)
    safe_addstr(stdscr, y + 9, max(0, (width - 46) // 2), "Hard: the deepest search budget in the cabinet", curses.A_DIM)

    stats = (
        f"W {state.stats['wins'][state.difficulty_key]}  "
        f"L {state.stats['losses'][state.difficulty_key]}  "
        f"D {state.stats['draws'][state.difficulty_key]}"
    )
    safe_addstr(stdscr, y + 12, max(0, (width - len(stats)) // 2), stats, accent_attr)

    footer = "←/→ or 1/2/3 choose level   Enter start   Q quit"
    safe_addstr(stdscr, height - 2, max(0, (width - len(footer)) // 2), footer, curses.A_DIM)
    if state.message:
        safe_addstr(stdscr, height - 4, max(0, (width - len(state.message)) // 2), state.message, accent_attr)
    stdscr.refresh()


def render_board(stdscr, state: GameState, has_color: bool) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    accent_attr = curses.color_pair(1) | curses.A_BOLD if has_color else curses.A_BOLD
    success_attr = curses.color_pair(3) | curses.A_BOLD if has_color else curses.A_BOLD
    danger_attr = curses.color_pair(6) | curses.A_BOLD if has_color else curses.A_BOLD
    box_attr = curses.color_pair(4) if has_color else curses.A_DIM

    origin_x = max(2, (width - 68) // 2)
    origin_y = 2

    safe_addstr(stdscr, origin_y, origin_x + 6, "A  B  C  D  E  F  G  H", accent_attr)
    for row in range(8):
        rank_label = str(8 - row)
        safe_addstr(stdscr, origin_y + 2 + row * 2, origin_x, rank_label, accent_attr)
        for col in range(8):
            token = board_token(state.position.board[row][col], row, col)
            safe_addstr(stdscr, origin_y + 2 + row * 2, origin_x + 4 + col * 4, token, box_attr)
        safe_addstr(stdscr, origin_y + 2 + row * 2, origin_x + 38, rank_label, accent_attr)
    safe_addstr(stdscr, origin_y + 18, origin_x + 6, "A  B  C  D  E  F  G  H", accent_attr)

    side = "White" if state.position.white_to_move else "Black"
    difficulty = DIFFICULTIES[state.difficulty_key]
    legal_count = len(generate_legal_moves(state.position))
    info_x = origin_x + 46
    safe_addstr(stdscr, origin_y + 2, info_x, f"Turn: {side}", accent_attr)
    safe_addstr(stdscr, origin_y + 4, info_x, f"Level: {difficulty.label}", accent_attr)
    safe_addstr(stdscr, origin_y + 6, info_x, f"Legal moves: {legal_count}", success_attr)
    safe_addstr(stdscr, origin_y + 8, info_x, f"Fullmove: {state.position.fullmove_number}", curses.A_DIM)
    safe_addstr(stdscr, origin_y + 9, info_x, f"Halfmove: {state.position.halfmove_clock}", curses.A_DIM)

    if state.thinking:
        safe_addstr(stdscr, origin_y + 11, info_x, "Engine thinking...", danger_attr)
    else:
        safe_addstr(stdscr, origin_y + 11, info_x, "Your move" if state.position.white_to_move else "Engine to move", success_attr)

    if state.position.history:
        last_move = state.position.history[-1].move.uci
        safe_addstr(stdscr, origin_y + 13, info_x, f"Last move: {last_move}", accent_attr)

    safe_addstr(stdscr, origin_y + 15, info_x, "Commands", accent_attr)
    safe_addstr(stdscr, origin_y + 16, info_x, "e2e4  move", curses.A_DIM)
    safe_addstr(stdscr, origin_y + 17, info_x, "undo  take back", curses.A_DIM)
    safe_addstr(stdscr, origin_y + 18, info_x, "new   restart", curses.A_DIM)
    safe_addstr(stdscr, origin_y + 19, info_x, "resign  concede", curses.A_DIM)
    safe_addstr(stdscr, origin_y + 20, info_x, "q  quit cabinet", curses.A_DIM)

    prompt = f"> {state.input_buffer}"
    safe_addstr(stdscr, height - 4, 2, prompt, accent_attr)

    message_attr = danger_attr if "Illegal" in state.message or "Unknown" in state.message else success_attr
    if state.message:
        safe_addstr(stdscr, height - 3, 2, state.message, message_attr)

    if state.screen == "gameover":
        safe_addstr(stdscr, height - 6, 2, state.result_text, danger_attr)
        safe_addstr(stdscr, height - 2, 2, "Enter starts a new game. Q quits.", curses.A_DIM)
    else:
        safe_addstr(stdscr, height - 2, 2, "Type a move and press Enter. Backspace edits. Q quits.", curses.A_DIM)
    stdscr.refresh()


def process_command(state: GameState, command: str) -> None:
    text = command.strip().lower()
    if not text:
        state.message = "Type a move like e2e4 or a command."
        return
    if text in {"q", "quit", "exit"}:
        state.running = False
        return
    if text == "new":
        start_new_game(state)
        return
    if text == "resign":
        apply_outcome(state, "black", "You resigned")
        return
    if text == "undo":
        if not state.position.history:
            state.message = "Nothing to undo."
            return
        if state.position.white_to_move and len(state.position.history) >= 2:
            undo_move(state.position)
            undo_move(state.position)
            state.message = "Undid the last full turn."
        elif not state.position.white_to_move:
            undo_move(state.position)
            state.message = "Undid your move."
        else:
            state.message = "Nothing to undo."
        state.screen = "playing"
        state.result_text = ""
        state.stats_recorded = False
        return

    if state.screen == "gameover":
        state.message = "Press Enter for a new game or Q to quit."
        return
    if not state.position.white_to_move:
        state.message = "Wait for the engine to move."
        return

    move = legal_move_from_text(state.position, text)
    if move is None:
        state.message = "Illegal or unknown move. Use UCI like e2e4 or e7e8q."
        return

    from .core import apply_move

    apply_move(state.position, move)
    state.message = f"You played {move.uci}."
    state.last_move_time = time.perf_counter()
    outcome = game_outcome(state.position)
    if outcome:
        winner, reason = outcome
        apply_outcome(state, winner, reason)


def handle_title_input(stdscr, state: GameState) -> None:
    while True:
        key = stdscr.getch()
        if key == -1:
            return
        if key in (ord("q"), ord("Q"), 27):
            state.running = False
            return
        if key in (curses.KEY_LEFT, ord("h"), ord("H")):
            cycle_difficulty(state, -1)
        elif key in (curses.KEY_RIGHT, ord("l"), ord("L")):
            cycle_difficulty(state, 1)
        elif key == ord("1"):
            state.difficulty_key = "easy"
        elif key == ord("2"):
            state.difficulty_key = "medium"
        elif key == ord("3"):
            state.difficulty_key = "hard"
        elif key in (10, 13, curses.KEY_ENTER, ord(" ")):
            start_new_game(state)
            return


def handle_playing_input(stdscr, state: GameState) -> None:
    while True:
        key = stdscr.getch()
        if key == -1:
            return
        if key in (ord("q"), ord("Q"), 27):
            state.running = False
            return
        if key in (10, 13, curses.KEY_ENTER):
            if state.screen == "gameover" and not state.input_buffer:
                start_new_game(state)
                return
            command = state.input_buffer
            state.input_buffer = ""
            process_command(state, command)
            return
        if key in (curses.KEY_BACKSPACE, 127, 8):
            state.input_buffer = state.input_buffer[:-1]
            continue
        if 32 <= key <= 126 and len(state.input_buffer) < 20:
            state.input_buffer += chr(key)


def drive_engine_turn(state: GameState) -> None:
    if state.screen != "playing" or state.position.white_to_move:
        return
    state.thinking = True
    move = search_best_move(state.position, state.difficulty_key, rng=state.engine_rng)
    from .core import apply_move

    apply_move(state.position, move)
    state.thinking = False
    state.message = f"Engine played {move.uci}."
    outcome = game_outcome(state.position)
    if outcome:
        winner, reason = outcome
        apply_outcome(state, winner, reason)


def main(stdscr) -> None:
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.nodelay(True)
    stdscr.keypad(True)
    stdscr.timeout(100)
    has_color = init_colors()

    state = GameState()
    last_difficulty = state.stats.get("last_difficulty")
    if last_difficulty in DIFFICULTIES:
        state.difficulty_key = last_difficulty
    state.message = f"Starting on {DIFFICULTIES[state.difficulty_key].label}."

    while state.running:
        height, width = stdscr.getmaxyx()
        if height < MIN_HEIGHT or width < MIN_WIDTH:
            render_small_terminal(stdscr, height, width)
            key = stdscr.getch()
            if key in (ord("q"), ord("Q"), 27):
                break
            continue

        if state.screen == "title":
            render_title(stdscr, state, has_color)
            handle_title_input(stdscr, state)
        else:
            render_board(stdscr, state, has_color)
            handle_playing_input(stdscr, state)
            if state.running and state.screen == "playing" and not state.position.white_to_move:
                drive_engine_turn(state)


def run() -> None:
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
