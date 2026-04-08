"""Terminal art assets for Dino Run."""

from __future__ import annotations

from dataclasses import dataclass

from .generated_svg_frames import SVG_TYRANT_FRAMES


SPRITE_WIDTH = 21


def _pad_rows(*rows: str) -> list[str]:
    return [row.ljust(SPRITE_WIDTH)[:SPRITE_WIDTH] for row in rows]


RUN_LEGS = (
    _pad_rows("       ███   ██", "      ██▀    ▀▀"),
    _pad_rows("       ███  ███", "      ▀ ▀   ▀▀ "),
    _pad_rows("       ██  ███▀", "      ▀▀ ▀ ▀   "),
    _pad_rows("       ███  ██▀", "      ▀ ▀  ▀▀  "),
    _pad_rows("       ██  ███ ", "      ▀▀   ▀ ▀ "),
    _pad_rows("       ███   ██", "      ██▀    ▀▀"),
)
JUMP_LEGS = _pad_rows("        ██ ██", "        ▀▀ ▀▀")
APEX_LEGS = _pad_rows("        ████ ", "         ▀▀  ")
FALL_LEGS = _pad_rows("       ██████", "       ▀▀ ▀▀ ")
DUCK_LEGS = (
    _pad_rows("    ██████ ███", "   ▀▀      ▀▀"),
    _pad_rows("    █████ ███ ", "   ▀▀   ▀  ▀▀"),
)


@dataclass(frozen=True)
class DinosaurVariant:
    key: str
    name: str
    short_name: str
    blurb: str
    frames: dict[str, list[list[str]] | list[str]]


def _hit_face(face: str) -> str:
    return face.replace("◉", "x", 1)


def _build_frames(
    *,
    crest: str,
    face: str,
    face_run: str,
    jaw: str,
    jaw_run: str,
    torso: str,
    arm: str,
    duck_top: str,
    duck_face: str,
    duck_face_open: str,
    duck_body: str,
    roar_faces: tuple[str, str, str],
    roar_jaws: tuple[str, str, str],
) -> dict[str, list[list[str]] | list[str]]:
    upper_idle = _pad_rows(crest, face, jaw, torso, arm)
    upper_run_closed = _pad_rows(crest, face, jaw, torso, arm)
    upper_run_open = _pad_rows(crest, face_run, jaw_run, torso, arm)
    duck_closed = _pad_rows(duck_top, duck_face, duck_body)
    duck_open = _pad_rows(duck_top, duck_face_open, duck_body)

    run_frames = []
    for index, legs in enumerate(RUN_LEGS):
        upper = upper_run_closed if index % 2 == 0 else upper_run_open
        run_frames.append([*upper, *legs])

    return {
        "idle": [[*upper_idle, *RUN_LEGS[0]], [*upper_idle, *RUN_LEGS[4]]],
        "run": run_frames,
        "jump_up": [*upper_idle, *JUMP_LEGS],
        "apex": [*upper_idle, *APEX_LEGS],
        "fall": [*upper_idle, *FALL_LEGS],
        "duck": [[*duck_closed, *DUCK_LEGS[0]], [*duck_open, *DUCK_LEGS[1]]],
        "hit": [*_pad_rows(crest, _hit_face(face), jaw, torso, arm), *RUN_LEGS[0]],
        "roar": [
            [*_pad_rows(crest, roar_faces[0], roar_jaws[0], torso, arm), *RUN_LEGS[0]],
            [*_pad_rows(crest, roar_faces[1], roar_jaws[1], torso, arm), *RUN_LEGS[1]],
            [*_pad_rows(crest, roar_faces[2], roar_jaws[2], torso, arm), *RUN_LEGS[2]],
        ],
    }


def _svg_tyrant_frames() -> dict[str, list[list[str]] | list[str]]:
    """Use the generated Unicode frames derived from the SVG source asset."""

    return SVG_TYRANT_FRAMES


DINOSAURS = (
    DinosaurVariant(
        key="tyrant",
        name="Tyrant Rex",
        short_name="Tyrant",
        blurb="SVG-inspired rex with dorsal spikes and a wider jaw",
        frames=_svg_tyrant_frames(),
    ),
    DinosaurVariant(
        key="allosaur",
        name="Allosaur",
        short_name="Allo",
        blurb="balanced hunter with a deep skull",
        frames=_build_frames(
            crest="         ▄▄▄▄▄",
            face="     ▄████◉███\\___",
            face_run="     ▄████◉███\\__>",
            jaw="   ▄████████████_/",
            jaw_run="   ▄███████████__>",
            torso="    ▀███████████▄",
            arm="       ███  ████",
            duck_top="  ▄██████████████",
            duck_face="▄██████◉█████████\\",
            duck_face_open="▄██████◉████████_>",
            duck_body="   ███████  ████",
            roar_faces=(
                "     ▄████◉███\\\\__",
                "     ▄████◉███\\\\\\_",
                "     ▄████◉█████\\\\",
            ),
            roar_jaws=(
                "   ▄████████████\\_",
                "   ▄████████████\\__",
                "   ▄████████████__>",
            ),
        ),
    ),
    DinosaurVariant(
        key="ceratosaur",
        name="Ceratosaur",
        short_name="Cerato",
        blurb="nose horn and a leaner skull",
        frames=_build_frames(
            crest="          ▄█▄",
            face="      ▄███◉█████\\__",
            face_run="      ▄███◉█████\\_>",
            jaw="    ▄████████████_/",
            jaw_run="    ▄███████████__>",
            torso="     ▀███████████▄",
            arm="        ███  ████",
            duck_top="   ▄█████████████",
            duck_face=" ▄█████◉█████████\\",
            duck_face_open=" ▄█████◉████████_>",
            duck_body="    ███████  ███",
            roar_faces=(
                "      ▄███◉█████\\\\_",
                "      ▄███◉█████\\\\\\",
                "      ▄███◉███████\\",
            ),
            roar_jaws=(
                "    ▄███████████\\__",
                "    ▄████████████\\_",
                "    ▄████████████__>",
            ),
        ),
    ),
    DinosaurVariant(
        key="carnotaur",
        name="Carnotaur",
        short_name="Carno",
        blurb="bull horns and a blunt snout",
        frames=_build_frames(
            crest="        ▄█▀▀█▄",
            face="    ▄████◉██████\\_",
            face_run="    ▄████◉██████\\>",
            jaw="   ▄████████████_/",
            jaw_run="   ▄███████████__>",
            torso="    ▀███████████▄",
            arm="       ██   ████",
            duck_top="  ▄█▀███████████▄",
            duck_face="▄█████◉██████████\\",
            duck_face_open="▄█████◉█████████_>",
            duck_body="   ███████  ███ ",
            roar_faces=(
                "    ▄████◉██████\\\\",
                "    ▄████◉██████\\\\\\",
                "    ▄████◉████████\\",
            ),
            roar_jaws=(
                "   ▄███████████\\__",
                "   ▄████████████\\_",
                "   ▄████████████__>",
            ),
        ),
    ),
    DinosaurVariant(
        key="dilophosaur",
        name="Dilophosaur",
        short_name="Dilo",
        blurb="double crests and a narrow face",
        frames=_build_frames(
            crest="       ▄█▀  ▀█▄",
            face="    ▄███◉█████\\___",
            face_run="    ▄███◉█████\\__>",
            jaw="   ▄███████████_/",
            jaw_run="   ▄██████████__>",
            torso="    ▀██████████▄ ",
            arm="       ███  ███ ",
            duck_top="  ▄█▀██████████▄",
            duck_face="▄█████◉█████████\\",
            duck_face_open="▄█████◉████████_>",
            duck_body="   ██████   ███ ",
            roar_faces=(
                "    ▄███◉█████\\\\__",
                "    ▄███◉█████\\\\\\_",
                "    ▄███◉███████\\\\",
            ),
            roar_jaws=(
                "   ▄███████████\\_",
                "   ▄███████████\\__",
                "   ▄███████████__>",
            ),
        ),
    ),
    DinosaurVariant(
        key="monoloph",
        name="Monolophosaur",
        short_name="Mono",
        blurb="single crest and a compact bite",
        frames=_build_frames(
            crest="       ▄█████▄",
            face="    ▄███◉██████\\__",
            face_run="    ▄███◉██████\\_>",
            jaw="   ▄████████████_/",
            jaw_run="   ▄███████████__>",
            torso="    ▀███████████ ",
            arm="       ███  ████",
            duck_top="  ▄█████████████▄",
            duck_face="▄██████◉█████████\\",
            duck_face_open="▄██████◉████████_>",
            duck_body="   ███████  ████",
            roar_faces=(
                "    ▄███◉██████\\\\_",
                "    ▄███◉██████\\\\\\",
                "    ▄███◉████████\\",
            ),
            roar_jaws=(
                "   ▄███████████\\__",
                "   ▄████████████\\_",
                "   ▄████████████__>",
            ),
        ),
    ),
    DinosaurVariant(
        key="cryoloph",
        name="Cryolophosaur",
        short_name="Cryo",
        blurb="swept pompadour crest and a sharp jaw",
        frames=_build_frames(
            crest="      ▄████▀",
            face="    ▄███◉██████\\___",
            face_run="    ▄███◉██████\\__>",
            jaw="   ▄████████████_/",
            jaw_run="   ▄███████████__>",
            torso="    ▀███████████▌",
            arm="       ███  ████",
            duck_top="  ▄████▀████████▄",
            duck_face="▄██████◉█████████\\",
            duck_face_open="▄██████◉████████_>",
            duck_body="   ███████  ████",
            roar_faces=(
                "    ▄███◉██████\\\\__",
                "    ▄███◉██████\\\\\\_",
                "    ▄███◉████████\\\\",
            ),
            roar_jaws=(
                "   ▄███████████\\__",
                "   ▄████████████\\_",
                "   ▄████████████__>",
            ),
        ),
    ),
    DinosaurVariant(
        key="spinosaur",
        name="Spinosaur",
        short_name="Spino",
        blurb="long snout with a sail-backed silhouette",
        frames=_build_frames(
            crest="          ▄▄",
            face="    ▄████◉███████\\___",
            face_run="    ▄████◉███████\\__>",
            jaw="  ▄██████████████_/",
            jaw_run="  ▄█████████████__>",
            torso="   ▀███████████▆▆ ",
            arm="      ███   ████ ",
            duck_top=" ▄████████████████",
            duck_face="██████◉███████████\\",
            duck_face_open="██████◉██████████_>",
            duck_body="  ████████  ████ ",
            roar_faces=(
                "    ▄████◉███████\\\\__",
                "    ▄████◉███████\\\\\\_",
                "    ▄████◉█████████\\\\",
            ),
            roar_jaws=(
                "  ▄██████████████\\_",
                "  ▄██████████████\\__",
                "  ▄██████████████__>",
            ),
        ),
    ),
    DinosaurVariant(
        key="acro",
        name="Acrocanthosaur",
        short_name="Acro",
        blurb="tall dorsal ridge and a powerful stride",
        frames=_build_frames(
            crest="         ▄▄▄▄",
            face="    ▄████◉█████\\___",
            face_run="    ▄████◉█████\\__>",
            jaw="  ▄██████████████_/",
            jaw_run="  ▄█████████████__>",
            torso="  ▀███████████▆██ ",
            arm="      ███   ████ ",
            duck_top=" ▄███████████████▄",
            duck_face="██████◉██████████\\",
            duck_face_open="██████◉█████████_>",
            duck_body="  ████████  ████ ",
            roar_faces=(
                "    ▄████◉█████\\\\__",
                "    ▄████◉█████\\\\\\_",
                "    ▄████◉███████\\\\",
            ),
            roar_jaws=(
                "  ▄██████████████\\_",
                "  ▄██████████████\\__",
                "  ▄██████████████__>",
            ),
        ),
    ),
    DinosaurVariant(
        key="raptor",
        name="Raptor",
        short_name="Raptor",
        blurb="lean runner with a fast, narrow muzzle",
        frames=_build_frames(
            crest="         ▄▄",
            face="      ▄██◉█████\\___",
            face_run="      ▄██◉█████\\__>",
            jaw="    ▄███████████_/",
            jaw_run="    ▄██████████__>",
            torso="     ▀██████████ ",
            arm="        ██   ███ ",
            duck_top="   ▄████████████▄",
            duck_face=" ▄████◉██████████\\",
            duck_face_open=" ▄████◉█████████_>",
            duck_body="    ██████   ███ ",
            roar_faces=(
                "      ▄██◉█████\\\\__",
                "      ▄██◉█████\\\\\\_",
                "      ▄██◉███████\\\\",
            ),
            roar_jaws=(
                "    ▄███████████\\_",
                "    ▄███████████\\__",
                "    ▄███████████__>",
            ),
        ),
    ),
)

DINOSAUR_ORDER = tuple(variant.key for variant in DINOSAURS)
DEFAULT_DINOSAUR_KEY = DINOSAUR_ORDER[0]
DINOSAUR_BY_KEY = {variant.key: variant for variant in DINOSAURS}
DINOSAUR_NAMES = {variant.key: variant.name for variant in DINOSAURS}
DINOSAUR_SHORT_NAMES = {variant.key: variant.short_name for variant in DINOSAURS}
DINOSAUR_BLURBS = {variant.key: variant.blurb for variant in DINOSAURS}
DINOSAUR_FRAMES = {variant.key: variant.frames for variant in DINOSAURS}

HAZARD_SPRITES = {
    "desert_pad": [
        "  █ ",
        " ███",
        " █ █",
        "██ ██",
        " █ █",
    ],
    "desert_tall": [
        "   █  ",
        "   █  ",
        " ████ ",
        " █ ██ ",
        "██████",
        "  █ █ ",
        "  █ █ ",
    ],
    "desert_stump": [
        " ████ ",
        "██████",
        " ████ ",
        "  ██  ",
    ],
    "fossil_ribs": [
        " ▄▄▄▄▄▄ ",
        "█ █ █ ██",
        "█ █ █ ██",
        "▀▀▀▀▀▀▀ ",
        "  ▐▌    ",
    ],
    "fossil_spire": [
        "   ▄   ",
        "  ▄█▄  ",
        " ▄███▄ ",
        "▄█████▄",
        "  ██   ",
        "  ██   ",
    ],
    "fossil_heap": [
        " ▄▄▄▄▄ ",
        "█▄█▄█▄█",
        " ▀███▀ ",
        "  ▀▀   ",
    ],
    "basalt_spike": [
        "   █   ",
        "  ███  ",
        " ▐███▌ ",
        " █████ ",
        "███████",
        "  █ █  ",
        "  █ █  ",
    ],
    "basalt_vent": [
        "  ▄▄▄  ",
        " ████▄ ",
        "██████ ",
        " ▀██▀  ",
        "  ██   ",
    ],
    "basalt_shards": [
        "█  █  █",
        " ██ ██ ",
        " █████ ",
        "  ███  ",
        "  █ █  ",
    ],
}

SCAVENGER_FRAMES = [
    [
        "█     █",
        " █   █ ",
        " █████ ",
    ],
    [
        " █████ ",
        "█     █",
        "   █   ",
    ],
]

BIOME_GROUNDS = {
    "scrub": {
        "flat": "__.___..___.___..__",
        "rough": "_.^._~._.^~.__.^._",
    },
    "fossil": {
        "flat": "==..::...::..==....",
        "rough": "=~==::=*=::==.~==..",
    },
    "basalt": {
        "flat": "##..###..##..###..#",
        "rough": "#^##..#^..##.^##..#",
    },
}

BIOME_LABELS = {
    "scrub": "Scrub Desert",
    "fossil": "Fern Grove",
    "basalt": "Basalt Night",
}

BIOME_SKYLINES = {
    "scrub": ["     sun over dunes     ", "   mesas in the haze    "],
    "fossil": ["    grove tree line     ", "   layered fern ridge   "],
    "basalt": ["    moon above crags    ", "   ridge and ash plume  "],
}

BIOME_BACKDROP_TILES = {
    "scrub": [
        "      __        ____        __      ",
        "  ___/  \\___   /    \\___  _/  \\__   ",
        "_/  c  |  _/__/  c   _/__/  | c  \\_ ",
    ],
    "fossil": [
        "      /\\         /\\         /\\      ",
        "    _/**\\_     _/**\\_     _/**\\_    ",
        "  _/||||||\\___/||||||\\___/||||||\\_  ",
    ],
    "basalt": [
        "        /\\          /\\          /\\   ",
        "   /\\___/  \\__/\\___/  \\__/\\___/  \\_  ",
        "_ /  sharp   __ sharp   __ sharp   \\ ",
    ],
}
