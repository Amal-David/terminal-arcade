"""Core chess rules and search engine for the terminal arcade cabinet."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
import time


FILES = "abcdefgh"
RANKS = "12345678"
WHITE_PIECES = set("PNBRQK")
BLACK_PIECES = set("pnbrqk")
KNIGHT_STEPS = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
BISHOP_DIRS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
ROOK_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS
KING_STEPS = QUEEN_DIRS

PIECE_VALUES = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

PAWN_TABLE = [
    0, 0, 0, 0, 0, 0, 0, 0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    6, 8, 14, 24, 24, 14, 8, 6,
    2, 4, 8, 18, 18, 8, 4, 2,
    4, -2, -6, 0, 0, -6, -2, 4,
    4, 8, 8, -16, -16, 8, 8, 4,
    0, 0, 0, 0, 0, 0, 0, 0,
]
KNIGHT_TABLE = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 2, 2, 0, -20, -40,
    -30, 2, 14, 18, 18, 14, 2, -30,
    -30, 6, 18, 24, 24, 18, 6, -30,
    -30, 4, 16, 24, 24, 16, 4, -30,
    -30, 0, 10, 16, 16, 10, 0, -30,
    -40, -20, -2, 0, 0, -2, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]
BISHOP_TABLE = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 4, 0, 0, 0, 0, 4, -10,
    -10, 8, 10, 12, 12, 10, 8, -10,
    -10, 0, 12, 18, 18, 12, 0, -10,
    -10, 2, 10, 18, 18, 10, 2, -10,
    -10, 6, 8, 12, 12, 8, 6, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]
ROOK_TABLE = [
    0, 0, 0, 4, 4, 0, 0, 0,
    -4, 0, 0, 0, 0, 0, 0, -4,
    -4, 0, 0, 0, 0, 0, 0, -4,
    -4, 0, 0, 0, 0, 0, 0, -4,
    -4, 0, 0, 0, 0, 0, 0, -4,
    -4, 0, 0, 0, 0, 0, 0, -4,
    4, 10, 10, 10, 10, 10, 10, 4,
    0, 0, 0, 4, 4, 0, 0, 0,
]
QUEEN_TABLE = [
    -20, -10, -10, -4, -4, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 6, 6, 6, 6, 0, -10,
    -4, 0, 6, 6, 6, 6, 0, -4,
    0, 0, 6, 6, 6, 6, 0, -4,
    -10, 6, 6, 6, 6, 6, 0, -10,
    -10, 0, 6, 0, 0, 0, 0, -10,
    -20, -10, -10, -4, -4, -10, -10, -20,
]
KING_MID_TABLE = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, -4, -4, -4, -4, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20,
]
KING_END_TABLE = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10, 0, 0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30, 0, 0, 0, 0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50,
]
TABLES = {
    "P": PAWN_TABLE,
    "N": KNIGHT_TABLE,
    "B": BISHOP_TABLE,
    "R": ROOK_TABLE,
    "Q": QUEEN_TABLE,
}

MATE_SCORE = 100_000
DRAW_SCORE = 0


@dataclass(frozen=True)
class Move:
    from_row: int
    from_col: int
    to_row: int
    to_col: int
    promotion: str | None = None

    @property
    def uci(self) -> str:
        suffix = self.promotion.lower() if self.promotion else ""
        return (
            square_name(self.from_row, self.from_col)
            + square_name(self.to_row, self.to_col)
            + suffix
        )


@dataclass
class UndoState:
    move: Move
    moved_piece: str
    captured_piece: str | None
    castling: str
    en_passant: tuple[int, int] | None
    halfmove_clock: int
    fullmove_number: int
    repetition_key: str
    was_en_passant: bool = False
    rook_from: tuple[int, int] | None = None
    rook_to: tuple[int, int] | None = None


@dataclass
class Position:
    board: list[list[str]] = field(default_factory=list)
    white_to_move: bool = True
    castling: str = "KQkq"
    en_passant: tuple[int, int] | None = None
    halfmove_clock: int = 0
    fullmove_number: int = 1
    history: list[UndoState] = field(default_factory=list)
    position_counts: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.board:
            self.board = initial_board()
        if not self.position_counts:
            self.position_counts = {position_key(self): 1}

    def clone(self) -> Position:
        return Position(
            board=[row[:] for row in self.board],
            white_to_move=self.white_to_move,
            castling=self.castling,
            en_passant=self.en_passant,
            halfmove_clock=self.halfmove_clock,
            fullmove_number=self.fullmove_number,
            history=list(self.history),
            position_counts=dict(self.position_counts),
        )


@dataclass(frozen=True)
class Difficulty:
    key: str
    label: str
    max_depth: int
    time_limit: float
    node_limit: int
    randomness: int


DIFFICULTIES = {
    "easy": Difficulty("easy", "Easy", max_depth=2, time_limit=0.15, node_limit=5_000, randomness=90),
    "medium": Difficulty("medium", "Medium", max_depth=3, time_limit=0.45, node_limit=20_000, randomness=0),
    "hard": Difficulty("hard", "Hard", max_depth=4, time_limit=1.2, node_limit=80_000, randomness=0),
}


class SearchTimeout(RuntimeError):
    """Raised when the engine search budget is exhausted."""


def initial_board() -> list[list[str]]:
    return [
        list("rnbqkbnr"),
        list("pppppppp"),
        list("........"),
        list("........"),
        list("........"),
        list("........"),
        list("PPPPPPPP"),
        list("RNBQKBNR"),
    ]


def square_name(row: int, col: int) -> str:
    return f"{FILES[col]}{8 - row}"


def parse_square(text: str) -> tuple[int, int]:
    file_name, rank_name = text[0], text[1]
    col = FILES.index(file_name)
    row = 8 - int(rank_name)
    return row, col


def inside(row: int, col: int) -> bool:
    return 0 <= row < 8 and 0 <= col < 8


def piece_color(piece: str) -> bool | None:
    if piece in WHITE_PIECES:
        return True
    if piece in BLACK_PIECES:
        return False
    return None


def capturable_enemy(target: str, white: bool) -> bool:
    return target != "." and piece_color(target) != white and target.upper() != "K"


def mirrored_index(row: int, col: int) -> int:
    return (7 - row) * 8 + col


def table_score(piece: str, row: int, col: int, endgame: bool) -> int:
    upper = piece.upper()
    if upper == "K":
        table = KING_END_TABLE if endgame else KING_MID_TABLE
    else:
        table = TABLES[upper]
    idx = row * 8 + col if piece.isupper() else mirrored_index(row, col)
    return table[idx]


def from_fen(fen: str) -> Position:
    parts = fen.split()
    board_part = parts[0]
    white_to_move = parts[1] == "w"
    castling = "" if parts[2] == "-" else parts[2]
    en_passant = None if parts[3] == "-" else parse_square(parts[3])
    halfmove = int(parts[4])
    fullmove = int(parts[5])

    board: list[list[str]] = []
    for rank in board_part.split("/"):
        row: list[str] = []
        for char in rank:
            if char.isdigit():
                row.extend("." for _ in range(int(char)))
            else:
                row.append(char)
        board.append(row)
    return Position(
        board=board,
        white_to_move=white_to_move,
        castling=castling,
        en_passant=en_passant,
        halfmove_clock=halfmove,
        fullmove_number=fullmove,
        history=[],
        position_counts={},
    )


def position_key(position: Position) -> str:
    board_key = "".join("".join(row) for row in position.board)
    side = "w" if position.white_to_move else "b"
    castling = position.castling or "-"
    ep = "-" if position.en_passant is None else square_name(*position.en_passant)
    return f"{board_key}|{side}|{castling}|{ep}"


def locate_king(position: Position, white: bool) -> tuple[int, int]:
    target = "K" if white else "k"
    for row in range(8):
        for col in range(8):
            if position.board[row][col] == target:
                return row, col
    raise ValueError("king missing from board")


def is_square_attacked(position: Position, row: int, col: int, by_white: bool) -> bool:
    pawn = "P" if by_white else "p"
    pawn_rows = ((row + 1, col - 1), (row + 1, col + 1)) if by_white else ((row - 1, col - 1), (row - 1, col + 1))
    for prow, pcol in pawn_rows:
        if inside(prow, pcol) and position.board[prow][pcol] == pawn:
            return True

    knight = "N" if by_white else "n"
    for drow, dcol in KNIGHT_STEPS:
        nrow, ncol = row + drow, col + dcol
        if inside(nrow, ncol) and position.board[nrow][ncol] == knight:
            return True

    bishop_targets = {"B", "Q"} if by_white else {"b", "q"}
    rook_targets = {"R", "Q"} if by_white else {"r", "q"}
    king = "K" if by_white else "k"

    for drow, dcol in BISHOP_DIRS:
        c_row, c_col = row + drow, col + dcol
        while inside(c_row, c_col):
            piece = position.board[c_row][c_col]
            if piece != ".":
                if piece in bishop_targets:
                    return True
                break
            c_row += drow
            c_col += dcol

    for drow, dcol in ROOK_DIRS:
        c_row, c_col = row + drow, col + dcol
        while inside(c_row, c_col):
            piece = position.board[c_row][c_col]
            if piece != ".":
                if piece in rook_targets:
                    return True
                break
            c_row += drow
            c_col += dcol

    for drow, dcol in KING_STEPS:
        krow, kcol = row + drow, col + dcol
        if inside(krow, kcol) and position.board[krow][kcol] == king:
            return True
    return False


def in_check(position: Position, white: bool) -> bool:
    king_row, king_col = locate_king(position, white)
    return is_square_attacked(position, king_row, king_col, not white)


def create_move(from_row: int, from_col: int, to_row: int, to_col: int, promotion: str | None = None) -> Move:
    return Move(from_row, from_col, to_row, to_col, promotion.upper() if promotion else None)


def parse_move(text: str) -> Move | None:
    cleaned = text.strip().lower().replace(" ", "")
    if len(cleaned) not in (4, 5):
        return None
    if cleaned[0] not in FILES or cleaned[2] not in FILES:
        return None
    if cleaned[1] not in RANKS or cleaned[3] not in RANKS:
        return None
    if len(cleaned) == 5 and cleaned[4] not in "qrbn":
        return None
    from_row, from_col = parse_square(cleaned[:2])
    to_row, to_col = parse_square(cleaned[2:4])
    promotion = cleaned[4].upper() if len(cleaned) == 5 else None
    return Move(from_row, from_col, to_row, to_col, promotion)


def move_matches(a: Move, b: Move) -> bool:
    return (
        a.from_row == b.from_row
        and a.from_col == b.from_col
        and a.to_row == b.to_row
        and a.to_col == b.to_col
        and (a.promotion or "") == (b.promotion or "")
    )


def legal_move_from_text(position: Position, text: str) -> Move | None:
    parsed = parse_move(text)
    if parsed is None:
        return None
    for move in generate_legal_moves(position):
        if move_matches(move, parsed):
            return move
    return None


def generate_pseudo_moves(position: Position, captures_only: bool = False) -> list[Move]:
    white = position.white_to_move
    moves: list[Move] = []
    for row in range(8):
        for col in range(8):
            piece = position.board[row][col]
            if piece == "." or piece_color(piece) != white:
                continue
            upper = piece.upper()
            if upper == "P":
                moves.extend(generate_pawn_moves(position, row, col, captures_only))
            elif upper == "N":
                for drow, dcol in KNIGHT_STEPS:
                    nrow, ncol = row + drow, col + dcol
                    if not inside(nrow, ncol):
                        continue
                    target = position.board[nrow][ncol]
                    if target == "." and captures_only:
                        continue
                    if target == "." or capturable_enemy(target, white):
                        moves.append(create_move(row, col, nrow, ncol))
            elif upper in {"B", "R", "Q"}:
                dirs = BISHOP_DIRS if upper == "B" else ROOK_DIRS if upper == "R" else QUEEN_DIRS
                moves.extend(generate_slider_moves(position, row, col, dirs, captures_only))
            elif upper == "K":
                for drow, dcol in KING_STEPS:
                    krow, kcol = row + drow, col + dcol
                    if not inside(krow, kcol):
                        continue
                    target = position.board[krow][kcol]
                    if target == "." and captures_only:
                        continue
                    if target == "." or piece_color(target) != white:
                        moves.append(create_move(row, col, krow, kcol))
                if not captures_only:
                    moves.extend(generate_castling_moves(position, row, col))
    return moves


def generate_slider_moves(
    position: Position,
    row: int,
    col: int,
    directions: tuple[tuple[int, int], ...],
    captures_only: bool,
) -> list[Move]:
    white = position.white_to_move
    moves: list[Move] = []
    for drow, dcol in directions:
        nrow, ncol = row + drow, col + dcol
        while inside(nrow, ncol):
            target = position.board[nrow][ncol]
            if target == ".":
                if not captures_only:
                    moves.append(create_move(row, col, nrow, ncol))
            else:
                if capturable_enemy(target, white):
                    moves.append(create_move(row, col, nrow, ncol))
                break
            nrow += drow
            ncol += dcol
    return moves


def generate_pawn_moves(position: Position, row: int, col: int, captures_only: bool) -> list[Move]:
    piece = position.board[row][col]
    white = piece.isupper()
    direction = -1 if white else 1
    start_row = 6 if white else 1
    promotion_row = 0 if white else 7
    moves: list[Move] = []

    next_row = row + direction
    if inside(next_row, col) and position.board[next_row][col] == "." and not captures_only:
        if next_row == promotion_row:
            for promo in "QRBN":
                moves.append(create_move(row, col, next_row, col, promo))
        else:
            moves.append(create_move(row, col, next_row, col))
        jump_row = row + direction * 2
        if row == start_row and position.board[jump_row][col] == ".":
            moves.append(create_move(row, col, jump_row, col))

    for dcol in (-1, 1):
        c_row, c_col = row + direction, col + dcol
        if not inside(c_row, c_col):
            continue
        target = position.board[c_row][c_col]
        if capturable_enemy(target, white):
            if c_row == promotion_row:
                for promo in "QRBN":
                    moves.append(create_move(row, col, c_row, c_col, promo))
            else:
                moves.append(create_move(row, col, c_row, c_col))
        elif position.en_passant == (c_row, c_col):
            moves.append(create_move(row, col, c_row, c_col))
    return moves


def generate_castling_moves(position: Position, row: int, col: int) -> list[Move]:
    if in_check(position, position.white_to_move):
        return []

    piece = position.board[row][col]
    white = piece.isupper()
    rights = position.castling
    moves: list[Move] = []
    if white and row == 7 and col == 4:
        if "K" in rights and position.board[7][5] == "." and position.board[7][6] == ".":
            if not is_square_attacked(position, 7, 5, False) and not is_square_attacked(position, 7, 6, False):
                moves.append(create_move(7, 4, 7, 6))
        if "Q" in rights and position.board[7][3] == "." and position.board[7][2] == "." and position.board[7][1] == ".":
            if not is_square_attacked(position, 7, 3, False) and not is_square_attacked(position, 7, 2, False):
                moves.append(create_move(7, 4, 7, 2))
    if not white and row == 0 and col == 4:
        if "k" in rights and position.board[0][5] == "." and position.board[0][6] == ".":
            if not is_square_attacked(position, 0, 5, True) and not is_square_attacked(position, 0, 6, True):
                moves.append(create_move(0, 4, 0, 6))
        if "q" in rights and position.board[0][3] == "." and position.board[0][2] == "." and position.board[0][1] == ".":
            if not is_square_attacked(position, 0, 3, True) and not is_square_attacked(position, 0, 2, True):
                moves.append(create_move(0, 4, 0, 2))
    return moves


def generate_legal_moves(position: Position, captures_only: bool = False) -> list[Move]:
    legal: list[Move] = []
    for move in generate_pseudo_moves(position, captures_only):
        undo = apply_move(position, move)
        if not in_check(position, not position.white_to_move):
            legal.append(move)
        undo_move(position)
        assert undo is not None
    return legal


def remove_castling_right(rights: str, flags: str) -> str:
    for flag in flags:
        rights = rights.replace(flag, "")
    return rights


def apply_move(position: Position, move: Move) -> UndoState:
    piece = position.board[move.from_row][move.from_col]
    target = position.board[move.to_row][move.to_col]
    white = piece.isupper()
    prev_key = position_key(position)

    undo = UndoState(
        move=move,
        moved_piece=piece,
        captured_piece=None if target == "." else target,
        castling=position.castling,
        en_passant=position.en_passant,
        halfmove_clock=position.halfmove_clock,
        fullmove_number=position.fullmove_number,
        repetition_key=prev_key,
    )

    position.board[move.from_row][move.from_col] = "."
    is_pawn = piece.upper() == "P"
    is_king = piece.upper() == "K"

    if is_pawn and position.en_passant == (move.to_row, move.to_col) and target == "." and move.from_col != move.to_col:
        cap_row = move.to_row + 1 if white else move.to_row - 1
        undo.captured_piece = position.board[cap_row][move.to_col]
        position.board[cap_row][move.to_col] = "."
        undo.was_en_passant = True

    if is_king and abs(move.to_col - move.from_col) == 2:
        rook_from_col, rook_to_col = (7, 5) if move.to_col > move.from_col else (0, 3)
        undo.rook_from = (move.from_row, rook_from_col)
        undo.rook_to = (move.from_row, rook_to_col)
        rook_piece = position.board[move.from_row][rook_from_col]
        position.board[move.from_row][rook_from_col] = "."
        position.board[move.from_row][rook_to_col] = rook_piece

    placed = piece
    if move.promotion:
        placed = move.promotion if white else move.promotion.lower()
    position.board[move.to_row][move.to_col] = placed

    if is_king:
        position.castling = remove_castling_right(position.castling, "KQ" if white else "kq")
    elif piece.upper() == "R":
        if (move.from_row, move.from_col) == (7, 0):
            position.castling = remove_castling_right(position.castling, "Q")
        elif (move.from_row, move.from_col) == (7, 7):
            position.castling = remove_castling_right(position.castling, "K")
        elif (move.from_row, move.from_col) == (0, 0):
            position.castling = remove_castling_right(position.castling, "q")
        elif (move.from_row, move.from_col) == (0, 7):
            position.castling = remove_castling_right(position.castling, "k")

    if undo.captured_piece and undo.captured_piece.upper() == "R":
        if (move.to_row, move.to_col) == (7, 0):
            position.castling = remove_castling_right(position.castling, "Q")
        elif (move.to_row, move.to_col) == (7, 7):
            position.castling = remove_castling_right(position.castling, "K")
        elif (move.to_row, move.to_col) == (0, 0):
            position.castling = remove_castling_right(position.castling, "q")
        elif (move.to_row, move.to_col) == (0, 7):
            position.castling = remove_castling_right(position.castling, "k")

    position.en_passant = None
    if is_pawn and abs(move.to_row - move.from_row) == 2:
        position.en_passant = ((move.from_row + move.to_row) // 2, move.from_col)

    if is_pawn or undo.captured_piece is not None:
        position.halfmove_clock = 0
    else:
        position.halfmove_clock += 1

    if not position.white_to_move:
        position.fullmove_number += 1
    position.white_to_move = not position.white_to_move

    new_key = position_key(position)
    position.position_counts[new_key] = position.position_counts.get(new_key, 0) + 1
    position.history.append(undo)
    return undo


def undo_move(position: Position) -> UndoState:
    undo = position.history.pop()
    current_key = position_key(position)
    count = position.position_counts.get(current_key, 0)
    if count <= 1:
        position.position_counts.pop(current_key, None)
    else:
        position.position_counts[current_key] = count - 1

    position.white_to_move = not position.white_to_move
    position.castling = undo.castling
    position.en_passant = undo.en_passant
    position.halfmove_clock = undo.halfmove_clock
    position.fullmove_number = undo.fullmove_number

    position.board[undo.move.from_row][undo.move.from_col] = undo.moved_piece
    position.board[undo.move.to_row][undo.move.to_col] = "."

    if undo.rook_from and undo.rook_to:
        rook_piece = position.board[undo.rook_to[0]][undo.rook_to[1]]
        position.board[undo.rook_to[0]][undo.rook_to[1]] = "."
        position.board[undo.rook_from[0]][undo.rook_from[1]] = rook_piece

    if undo.was_en_passant:
        cap_row = undo.move.to_row + 1 if undo.moved_piece.isupper() else undo.move.to_row - 1
        position.board[cap_row][undo.move.to_col] = undo.captured_piece or "."
    elif undo.captured_piece:
        position.board[undo.move.to_row][undo.move.to_col] = undo.captured_piece
    return undo


def is_capture(position: Position, move: Move) -> bool:
    piece = position.board[move.from_row][move.from_col]
    target = position.board[move.to_row][move.to_col]
    if target != ".":
        return True
    return piece.upper() == "P" and move.from_col != move.to_col and position.en_passant == (move.to_row, move.to_col)


def move_priority(position: Position, move: Move, tt_move: Move | None = None) -> int:
    if tt_move and move_matches(move, tt_move):
        return 1_000_000
    score = 0
    if is_capture(position, move):
        attacker = position.board[move.from_row][move.from_col].upper()
        target = position.board[move.to_row][move.to_col]
        if target == ".":
            target = "P"
        score += 10_000 + PIECE_VALUES[target.upper()] - PIECE_VALUES[attacker] // 10
    if move.promotion:
        score += 8_000 + PIECE_VALUES[move.promotion]
    if position.board[move.from_row][move.from_col].upper() == "K" and abs(move.to_col - move.from_col) == 2:
        score += 500
    return score


def ordered_moves(position: Position, captures_only: bool = False, tt_move: Move | None = None) -> list[Move]:
    moves = generate_legal_moves(position, captures_only)
    return sorted(moves, key=lambda move: move_priority(position, move, tt_move), reverse=True)


def game_outcome(position: Position) -> tuple[str, str] | None:
    key = position_key(position)
    if position.position_counts.get(key, 0) >= 3:
        return ("draw", "Draw by repetition")
    if position.halfmove_clock >= 100:
        return ("draw", "Draw by fifty-move rule")
    if is_insufficient_material(position):
        return ("draw", "Draw by insufficient material")

    legal = generate_legal_moves(position)
    if legal:
        return None
    if in_check(position, position.white_to_move):
        return ("black" if position.white_to_move else "white", "Checkmate")
    return ("draw", "Stalemate")


def is_insufficient_material(position: Position) -> bool:
    pieces = [piece for row in position.board for piece in row if piece != "."]
    non_kings = [piece for piece in pieces if piece.upper() != "K"]
    if not non_kings:
        return True
    if len(non_kings) == 1 and non_kings[0].upper() in {"B", "N"}:
        return True
    if all(piece.upper() == "B" for piece in non_kings) and len(non_kings) <= 2:
        return True
    return False


def mobility_count(position: Position, white: bool) -> int:
    current = position.white_to_move
    position.white_to_move = white
    count = len(generate_pseudo_moves(position, captures_only=False))
    position.white_to_move = current
    return count


def pawn_structure_score(position: Position, white: bool) -> int:
    pawn = "P" if white else "p"
    enemy_pawn = "p" if white else "P"
    pawns = [(row, col) for row in range(8) for col in range(8) if position.board[row][col] == pawn]
    score = 0
    files = [0] * 8
    for _, col in pawns:
        files[col] += 1

    for row, col in pawns:
        if files[col] > 1:
            score -= 12
        if col > 0 and files[col - 1] > 0:
            isolated = False
        elif col < 7 and files[col + 1] > 0:
            isolated = False
        else:
            isolated = True
        if isolated:
            score -= 10

        blocked = False
        for enemy_col in (col - 1, col, col + 1):
            if not 0 <= enemy_col < 8:
                continue
            scan_rows = range(row - 1, -1, -1) if white else range(row + 1, 8)
            for scan_row in scan_rows:
                if position.board[scan_row][enemy_col] == enemy_pawn:
                    blocked = True
                    break
            if blocked:
                break
        if not blocked:
            advance = 6 - row if white else row - 1
            score += 18 + advance * 5
    return score


def king_safety_score(position: Position, white: bool, endgame: bool) -> int:
    row, col = locate_king(position, white)
    if endgame:
        return 0
    shield_row = row - 1 if white else row + 1
    shield = 0
    for s_col in (col - 1, col, col + 1):
        if inside(shield_row, s_col):
            piece = position.board[shield_row][s_col]
            if piece == ("P" if white else "p"):
                shield += 12
    edge_penalty = 0 if col in (0, 1, 6, 7) else -8
    return shield + edge_penalty


def center_control_score(position: Position, white: bool) -> int:
    centers = {(3, 3), (3, 4), (4, 3), (4, 4)}
    score = 0
    for row in range(8):
        for col in range(8):
            piece = position.board[row][col]
            if piece == "." or piece_color(piece) != white:
                continue
            if (row, col) in centers:
                score += 8 if piece.upper() in {"P", "N", "B"} else 4
    return score


def evaluate(position: Position) -> int:
    outcome = game_outcome(position)
    if outcome:
        winner, reason = outcome
        if winner == "draw":
            return DRAW_SCORE
        mate_bias = -(MATE_SCORE - len(position.history))
        return mate_bias if position.white_to_move else -mate_bias

    pieces = [piece for row in position.board for piece in row if piece != "." and piece.upper() not in {"K", "P"}]
    endgame = sum(PIECE_VALUES[p.upper()] for p in pieces) <= 2_300

    white_score = 0
    black_score = 0
    white_bishops = 0
    black_bishops = 0

    for row in range(8):
        for col in range(8):
            piece = position.board[row][col]
            if piece == ".":
                continue
            base = PIECE_VALUES[piece.upper()]
            pst = table_score(piece, row, col, endgame)
            if piece.isupper():
                white_score += base + pst
                if piece == "B":
                    white_bishops += 1
            else:
                black_score += base + pst
                if piece == "b":
                    black_bishops += 1

    if white_bishops >= 2:
        white_score += 30
    if black_bishops >= 2:
        black_score += 30

    white_score += pawn_structure_score(position, True)
    black_score += pawn_structure_score(position, False)
    white_score += king_safety_score(position, True, endgame)
    black_score += king_safety_score(position, False, endgame)
    white_score += center_control_score(position, True)
    black_score += center_control_score(position, False)
    white_score += mobility_count(position, True) * 2
    black_score += mobility_count(position, False) * 2

    score = white_score - black_score
    return score if position.white_to_move else -score


@dataclass
class TTEntry:
    depth: int
    score: int
    flag: str
    best_move: Move | None


@dataclass
class SearchContext:
    difficulty: Difficulty
    deadline: float
    node_limit: int
    nodes: int = 0
    table: dict[str, TTEntry] = field(default_factory=dict)

    def tick(self) -> None:
        self.nodes += 1
        if self.nodes >= self.node_limit or time.perf_counter() > self.deadline:
            raise SearchTimeout


def quiescence(position: Position, alpha: int, beta: int, context: SearchContext) -> int:
    context.tick()
    stand_pat = evaluate(position)
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    for move in ordered_moves(position, captures_only=True):
        apply_move(position, move)
        score = -quiescence(position, -beta, -alpha, context)
        undo_move(position)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


def negamax(position: Position, depth: int, alpha: int, beta: int, context: SearchContext, ply: int = 0) -> int:
    context.tick()
    key = position_key(position)
    original_alpha = alpha
    entry = context.table.get(key)
    tt_move = None
    if entry and entry.depth >= depth:
        tt_move = entry.best_move
        if entry.flag == "exact":
            return entry.score
        if entry.flag == "lower":
            alpha = max(alpha, entry.score)
        elif entry.flag == "upper":
            beta = min(beta, entry.score)
        if alpha >= beta:
            return entry.score
    elif entry:
        tt_move = entry.best_move

    outcome = game_outcome(position)
    if outcome:
        winner, _ = outcome
        if winner == "draw":
            return DRAW_SCORE
        return -(MATE_SCORE - ply)

    if depth == 0:
        return quiescence(position, alpha, beta, context)

    best_score = -math.inf
    best_move = None
    moves = ordered_moves(position, captures_only=False, tt_move=tt_move)
    for move in moves:
        apply_move(position, move)
        score = -negamax(position, depth - 1, -beta, -alpha, context, ply + 1)
        undo_move(position)
        if score > best_score:
            best_score = score
            best_move = move
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    flag = "exact"
    if best_score <= original_alpha:
        flag = "upper"
    elif best_score >= beta:
        flag = "lower"
    context.table[key] = TTEntry(depth=depth, score=best_score, flag=flag, best_move=best_move)
    return best_score


def search_best_move(position: Position, difficulty_key: str, rng: random.Random | None = None) -> Move:
    difficulty = DIFFICULTIES[difficulty_key]
    rng = rng or random.Random()
    deadline = time.perf_counter() + difficulty.time_limit
    context = SearchContext(difficulty=difficulty, deadline=deadline, node_limit=difficulty.node_limit)

    root_moves = ordered_moves(position)
    if not root_moves:
        raise ValueError("no legal moves available")

    best_move = root_moves[0]
    best_score = -math.inf
    completed_scores: list[tuple[int, Move]] = []

    for depth in range(1, difficulty.max_depth + 1):
        try:
            scored: list[tuple[int, Move]] = []
            alpha = -math.inf
            beta = math.inf
            for move in ordered_moves(position, tt_move=best_move):
                apply_move(position, move)
                score = -negamax(position, depth - 1, -beta, -alpha, context, 1)
                undo_move(position)
                scored.append((score, move))
                if score > alpha:
                    alpha = score
            scored.sort(key=lambda item: item[0], reverse=True)
            best_score, best_move = scored[0]
            completed_scores = scored
        except SearchTimeout:
            break

    if difficulty.randomness and completed_scores:
        threshold = best_score - difficulty.randomness
        candidates = [move for score, move in completed_scores[:3] if score >= threshold]
        if candidates:
            return rng.choice(candidates)
    return best_move
