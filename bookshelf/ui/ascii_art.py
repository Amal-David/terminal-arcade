"""ASCII art for the bookshelf TUI."""

TITLE_ART = [
    r"  _____ _           ___            _        _          _  __  ",
    r" |_   _| |_  ___   | _ ) ___  ___ | |__ ___| |_  ___  | |/ _| ",
    r"   | | | ' \/ -_)  | _ \/ _ \/ _ \| / /(_-<| ' \/ -_) | |  _| ",
    r"   |_| |_||_\___|  |___/\___/\___/|_\_\/__/|_||_\___| |_|_|   ",
]

SHELF_TOP = "╔══════════════════════════════════════════════════════════════════════════╗"
SHELF_BOT = "╚══════════════════════════════════════════════════════════════════════════╝"
SHELF_DIV = "╠══════════════════════════════════════════════════════════════════════════╣"
SHELF_SIDE = "║"

BOOK_SPINE_TOP = "┌─────────────────┐"
BOOK_SPINE_BOT = "└─────────────────┘"
BOOK_SPINE_SIDE = "│"

OPEN_BOOK = [
    r"        _______________________        ",
    r"       /                       \       ",
    r"      /    ┌───────────────┐    \      ",
    r"     /     │               │     \     ",
    r"    /      │               │      \    ",
    r"   /       │               │       \   ",
    r"  /        │               │        \  ",
    r" /         │               │         \ ",
    r"|          │               │          |",
    r"|          └───────────────┘          |",
    r" \                                   / ",
    r"  \_________________________________/  ",
]

HEART_FULL = "♥"
HEART_EMPTY = "♡"

GENRE_ICONS = {
    "motivation": "★",
    "startup": "◆",
    "romance": "♥",
    "all": "●",
}


def truncate(text: str, width: int) -> str:
    """Truncate text to fit within width, adding ellipsis if needed."""
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"


def center_text(text: str, width: int) -> str:
    """Center text within the given width."""
    if len(text) >= width:
        return text[:width]
    pad = (width - len(text)) // 2
    return " " * pad + text


def wrap_text(text: str, width: int) -> list[str]:
    """Word-wrap text to fit within width."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        elif current:
            current += " " + word
        else:
            current = word
    if current:
        lines.append(current)
    return lines or [""]
