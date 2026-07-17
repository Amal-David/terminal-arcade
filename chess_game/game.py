"""Terminal chess cabinet with a built-in rule-based engine."""

from __future__ import annotations

import curses
from dataclasses import dataclass, field
import random
import time

from terminal_arcade.ui import hide_cursor, safe_addstr

from .core import (
    DIFFICULTIES,
    Position,
    game_outcome,
    generate_legal_moves,
    legal_move_from_text,
    search_best_move,
    square_name,
    undo_move,
)
from .storage import load_stats, save_stats


MIN_WIDTH = 108
MIN_HEIGHT = 48
SQUARE_W = 12
SQUARE_H = 5
SPRITE_W = 10
ENGINE_THINK_DELAY = 0.75
LOG_PANEL_W = 28
TITLE_ART = [
    "  ██████╗██╗  ██╗███████╗███████╗███████╗",
    " ██╔════╝██║  ██║██╔════╝██╔════╝██╔════╝",
    " ██║     ███████║█████╗  ███████╗███████╗",
    " ██║     ██╔══██║██╔══╝  ╚════██║╚════██║",
    " ╚██████╗██║  ██║███████╗███████║███████║",
    "  ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝",
]
LIGHT_FILL = "░"
DARK_FILL = "▒"
PIECE_SPRITES = {
    "P": (
        "    XX    ",
        "   XXXX   ",
        "    XX    ",
        "   XXXX   ",
        " XXXXXXXX ",
    ),
    "N": (
        "  XXXX    ",
        " XXXXXXX  ",
        "XX  XXXX  ",
        "    XXX   ",
        " XXXXXXXX ",
    ),
    "B": (
        "    XX    ",
        "   XXXX   ",
        "  XX  XX  ",
        "   XXXX   ",
        " XXXXXXXX ",
    ),
    "R": (
        "XX XXXX XX",
        "XXXXXXXXXX",
        "  XXXXXX  ",
        "  XXXXXX  ",
        "XXXXXXXXXX",
    ),
    "Q": (
        "XX  XX  XX",
        " XXXXXXXX ",
        " XXXXXX X ",
        "  XXXXXX  ",
        "XXXXXXXXXX",
    ),
    "K": (
        "   XXXX   ",
        "XX  XX  XX",
        " XXXXXXXX ",
        "   XXXX   ",
        "XXXXXXXXXX",
    ),
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
    cursor_row: int = 6
    cursor_col: int = 4
    selected_square: tuple[int, int] | None = None
    move_log: list[str] = field(default_factory=list)
    engine_move_due_at: float | None = None
    pending_engine_reply_ply: int | None = None


def append_log(state: GameState, text: str) -> None:
    state.move_log.append(text)
    state.move_log = state.move_log[-12:]


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
    curses.init_pair(7, curses.COLOR_WHITE, -1)
    curses.init_pair(8, curses.COLOR_BLUE, -1)
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
    append_log(state, state.result_text)
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
    state.message = "Move the cursor, select a piece, then choose a destination."
    state.result_text = ""
    state.thinking = False
    state.stats_recorded = False
    state.last_move_time = time.perf_counter()
    state.cursor_row = 6
    state.cursor_col = 4
    state.selected_square = None
    state.move_log = [f"New game: {DIFFICULTIES[state.difficulty_key].label}"]
    state.engine_move_due_at = None
    state.pending_engine_reply_ply = None
    state.stats["last_difficulty"] = state.difficulty_key
    save_stats(state.stats)


def cycle_difficulty(state: GameState, step: int) -> None:
    keys = list(DIFFICULTIES)
    index = keys.index(state.difficulty_key)
    state.difficulty_key = keys[(index + step) % len(keys)]
    state.message = f"Difficulty set to {DIFFICULTIES[state.difficulty_key].label}."


def square_fill(row: int, col: int) -> str:
    return LIGHT_FILL if (row + col) % 2 == 0 else DARK_FILL


def piece_sprite(piece: str) -> tuple[str, ...]:
    if piece == ".":
        return tuple(" " * SPRITE_W for _ in range(SQUARE_H))
    fill = "█" if piece.isupper() else "▓"
    return tuple(line.replace("X", fill) for line in PIECE_SPRITES[piece.upper()])


def legal_destinations_for_selection(state: GameState) -> set[tuple[int, int]]:
    if state.selected_square is None:
        return set()
    from_row, from_col = state.selected_square
    return {
        (move.to_row, move.to_col)
        for move in generate_legal_moves(state.position)
        if move.from_row == from_row and move.from_col == from_col
    }


def build_selected_move_text(state: GameState, to_row: int, to_col: int) -> str | None:
    if state.selected_square is None:
        return None
    from_row, from_col = state.selected_square
    text = square_name(from_row, from_col) + square_name(to_row, to_col)
    piece = state.position.board[from_row][from_col]
    if piece.upper() == "P" and to_row in {0, 7}:
        text += "q"
    return text


def move_cursor(state: GameState, drow: int, dcol: int) -> None:
    state.cursor_row = (state.cursor_row + drow) % 8
    state.cursor_col = (state.cursor_col + dcol) % 8


def clear_selection(state: GameState, message: str | None = None) -> None:
    state.selected_square = None
    if message is not None:
        state.message = message


def select_or_play_cursor_square(state: GameState) -> None:
    if state.screen == "gameover":
        start_new_game(state)
        return
    if not state.position.white_to_move:
        state.message = "Wait for the engine to move."
        return

    piece = state.position.board[state.cursor_row][state.cursor_col]
    if state.selected_square is None:
        if piece == "." or not piece.isupper():
            state.message = "Select one of your white pieces first."
            return
        state.selected_square = (state.cursor_row, state.cursor_col)
        state.message = f"Selected {square_name(*state.selected_square)}. Choose a destination."
        return

    if state.selected_square == (state.cursor_row, state.cursor_col):
        clear_selection(state, "Selection cleared.")
        return
    if piece != "." and piece.isupper():
        state.selected_square = (state.cursor_row, state.cursor_col)
        state.message = f"Selected {square_name(*state.selected_square)}. Choose a destination."
        return

    move_text = build_selected_move_text(state, state.cursor_row, state.cursor_col)
    if move_text is None:
        state.message = "No source square selected."
        return
    clear_selection(state)
    process_command(state, move_text)


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

    description = "Play White against the built-in engine on a big pixel board."
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

    footer = "Left/Right or 1/2/3 choose level   Enter start   Q quit"
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
    box_attr = curses.A_DIM
    cursor_attr = curses.color_pair(2) | curses.A_REVERSE | curses.A_BOLD if has_color else curses.A_REVERSE
    selected_attr = curses.color_pair(5) | curses.A_REVERSE | curses.A_BOLD if has_color else (curses.A_REVERSE | curses.A_BOLD)
    target_attr = curses.color_pair(3) | curses.A_BOLD if has_color else curses.A_BOLD
    white_piece_attr = curses.color_pair(7) | curses.A_BOLD if has_color else curses.A_BOLD
    black_piece_attr = curses.color_pair(8) | curses.A_BOLD if has_color else curses.A_BOLD

    board_w = 8 * SQUARE_W
    board_h = 8 * SQUARE_H
    show_log = width >= 138
    total_w = 3 + board_w + 3 + (LOG_PANEL_W + 3 if show_log else 0)
    origin_x = max(1, (width - total_w) // 2)
    board_x = origin_x + 3
    file_label_y = 3
    board_y = 4
    destinations = legal_destinations_for_selection(state)
    side = "White" if state.position.white_to_move else "Black"
    difficulty = DIFFICULTIES[state.difficulty_key]
    last_move = state.position.history[-1].move.uci if state.position.history else "--"
    cursor_square = square_name(state.cursor_row, state.cursor_col)
    from_square = square_name(*state.selected_square) if state.selected_square else "--"
    hud = (
        f"CHESS  Turn {side}  Level {difficulty.label}  "
        f"Last {last_move}  Cursor {cursor_square}  From {from_square}"
    )
    safe_addstr(stdscr, 1, max(1, (width - len(hud)) // 2), hud, accent_attr)

    for col, file_name in enumerate("A B C D E F G H".split()):
        safe_addstr(stdscr, file_label_y, board_x + col * SQUARE_W + SQUARE_W // 2, file_name, accent_attr)
    for row in range(8):
        rank_label = str(8 - row)
        square_y = board_y + row * SQUARE_H
        rank_y = square_y + SQUARE_H // 2
        safe_addstr(stdscr, rank_y, origin_x, rank_label, accent_attr)
        for col in range(8):
            square_x = board_x + col * SQUARE_W
            attr = box_attr
            if state.selected_square == (row, col):
                attr = selected_attr
            elif (state.cursor_row, state.cursor_col) == (row, col):
                attr = cursor_attr
            elif (row, col) in destinations:
                attr = target_attr

            for line in range(SQUARE_H):
                safe_addstr(stdscr, square_y + line, square_x, square_fill(row, col) * SQUARE_W, attr)

            piece = state.position.board[row][col]
            if piece != ".":
                piece_attr = white_piece_attr if piece.isupper() else black_piece_attr
                if attr in (cursor_attr, selected_attr):
                    piece_attr = attr
                for line, sprite_line in enumerate(piece_sprite(piece)):
                    sprite_x = square_x + (SQUARE_W - SPRITE_W) // 2
                    safe_addstr(stdscr, square_y + line, sprite_x, sprite_line, piece_attr)
            elif (row, col) in destinations:
                safe_addstr(stdscr, square_y + 2, square_x + SQUARE_W // 2, "◆", target_attr)
        safe_addstr(stdscr, rank_y, board_x + board_w + 2, rank_label, accent_attr)
    for col, file_name in enumerate("A B C D E F G H".split()):
        safe_addstr(stdscr, board_y + board_h, board_x + col * SQUARE_W + SQUARE_W // 2, file_name, accent_attr)

    if show_log:
        log_x = board_x + board_w + 5
        safe_addstr(stdscr, board_y, log_x, "Move log", accent_attr)
        for offset, entry in enumerate(state.move_log[-18:]):
            safe_addstr(stdscr, board_y + 2 + offset, log_x, entry[:LOG_PANEL_W], curses.A_DIM)

    legal_count = len(generate_legal_moves(state.position))
    bottom_y = board_y + board_h + 2
    state_line = f"Legal {legal_count}  Fullmove {state.position.fullmove_number}  Halfmove {state.position.halfmove_clock}"
    if state.thinking:
        state_line += "  Engine thinking..."
        state_attr = danger_attr
    else:
        state_line += "  Your move" if state.position.white_to_move else "  Engine to move"
        state_attr = success_attr
    safe_addstr(stdscr, bottom_y, max(1, (width - len(state_line)) // 2), state_line, state_attr)

    controls = "Arrows/hjkl move   Space/Enter select   X/Backspace cancel   type e2e4   undo new resign q"
    safe_addstr(stdscr, bottom_y + 1, max(1, (width - len(controls)) // 2), controls, curses.A_DIM)

    prompt = f"> {state.input_buffer}"
    if state.input_buffer:
        safe_addstr(stdscr, bottom_y + 2, max(1, (width - len(prompt)) // 2), prompt, accent_attr)

    message_attr = danger_attr if "Illegal" in state.message or "Unknown" in state.message else success_attr
    if state.message:
        safe_addstr(stdscr, height - 3, max(1, (width - len(state.message)) // 2), state.message, message_attr)

    if state.screen == "gameover":
        safe_addstr(stdscr, height - 5, max(1, (width - len(state.result_text)) // 2), state.result_text, danger_attr)
        safe_addstr(stdscr, height - 2, max(1, (width - 32) // 2), "Enter starts a new game. Q quits.", curses.A_DIM)
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
        clear_selection(state)
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
        state.engine_move_due_at = None
        state.pending_engine_reply_ply = None
        clear_selection(state)
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
    clear_selection(state)
    state.message = f"You played {move.uci}."
    append_log(state, f"You: {move.uci}")
    state.last_move_time = time.perf_counter()
    outcome = game_outcome(state.position)
    if outcome:
        winner, reason = outcome
        apply_outcome(state, winner, reason)
    elif not state.position.white_to_move:
        state.thinking = True
        state.pending_engine_reply_ply = len(state.position.history)
        state.engine_move_due_at = time.perf_counter() + ENGINE_THINK_DELAY


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
        if key in (curses.KEY_UP, ord("k"), ord("K")):
            move_cursor(state, -1, 0)
            continue
        if key in (curses.KEY_DOWN, ord("j"), ord("J")):
            move_cursor(state, 1, 0)
            continue
        if key in (curses.KEY_LEFT, ord("h"), ord("H")):
            move_cursor(state, 0, -1)
            continue
        if key in (curses.KEY_RIGHT, ord("l"), ord("L")):
            move_cursor(state, 0, 1)
            continue
        if key in (ord("x"), ord("X")):
            clear_selection(state, "Selection cleared.")
            continue
        if key in (10, 13, curses.KEY_ENTER):
            if not state.input_buffer:
                select_or_play_cursor_square(state)
                return
            if state.screen == "gameover":
                start_new_game(state)
                return
            command = state.input_buffer
            state.input_buffer = ""
            process_command(state, command)
            return
        if key == ord(" "):
            if state.input_buffer:
                state.input_buffer += " "
            else:
                select_or_play_cursor_square(state)
                return
            continue
        if key in (curses.KEY_BACKSPACE, 127, 8):
            if not state.input_buffer and state.selected_square is not None:
                clear_selection(state, "Selection cleared.")
                continue
            state.input_buffer = state.input_buffer[:-1]
            continue
        if 32 <= key <= 126 and len(state.input_buffer) < 20:
            state.input_buffer += chr(key)


def drive_engine_turn(state: GameState) -> None:
    if state.screen != "playing":
        return
    if state.position.white_to_move:
        state.thinking = False
        state.engine_move_due_at = None
        state.pending_engine_reply_ply = None
        return
    if state.pending_engine_reply_ply is None:
        state.thinking = False
        state.engine_move_due_at = None
        return
    if state.pending_engine_reply_ply != len(state.position.history):
        state.thinking = False
        state.engine_move_due_at = None
        state.pending_engine_reply_ply = None
        return
    now = time.perf_counter()
    if state.engine_move_due_at is None:
        state.engine_move_due_at = now + ENGINE_THINK_DELAY
        state.thinking = True
        state.message = "Engine is thinking..."
        return
    if now < state.engine_move_due_at:
        state.thinking = True
        state.message = "Engine is thinking..."
        return
    state.thinking = True
    move = search_best_move(state.position, state.difficulty_key, rng=state.engine_rng)
    from .core import apply_move

    apply_move(state.position, move)
    state.thinking = False
    state.engine_move_due_at = None
    state.pending_engine_reply_ply = None
    state.message = f"Engine played {move.uci}."
    append_log(state, f"Engine: {move.uci}")
    outcome = game_outcome(state.position)
    if outcome:
        winner, reason = outcome
        apply_outcome(state, winner, reason)


def main(stdscr) -> None:
    hide_cursor()
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
