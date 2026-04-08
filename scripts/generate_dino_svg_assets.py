#!/usr/bin/env python3
from __future__ import annotations

import copy
import re
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = REPO_ROOT / "assets" / "source"
SOURCE_SVG_PATH = SOURCE_DIR / "dinosaur_svg_sprite_animation.svg"
DOWNLOAD_HTML_PATH = Path.home() / "Downloads" / "dinosaur_svg_sprite_animation.html"
OUTPUT_PATH = REPO_ROOT / "dino_game" / "generated_svg_frames.py"

RENDER_WIDTH = 240
RENDER_HEIGHT = 128
TARGET_PIXEL_WIDTH = 44
TARGET_PIXEL_HEIGHT = 18
DARKNESS_THRESHOLD = 0.13

COLOR_STYLE = """
.dino-body { fill: #4a8c3f; }
.dino-dark { fill: #2d5a24; }
.dino-light { fill: #5ca04e; }
.dino-belly { fill: #c8d8a0; }
.dino-eye-w { fill: #ffffff; }
.dino-eye-p { fill: #1a1a1a; }
.dino-mouth { fill: #23421c; }
.dino-teeth { fill: #f0ece0; }
.dino-claw { fill: none; stroke: #d8cca8; stroke-width: 1.5; stroke-linecap: round; }
.dino-tongue { fill: #d46a6a; }
.dino-spike { fill: #3a7030; }
.dino-foot { fill: #315d28; }
""".strip()


@dataclass(frozen=True)
class FrameSpec:
    name: str
    transforms: dict[str, str] = field(default_factory=dict)
    show_tongue: bool = False
    hit_eye: bool = False


def svg_tag(name: str) -> str:
    return f"{{{SVG_NS}}}{name}"


def ensure_source_svg() -> Path:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    if SOURCE_SVG_PATH.exists():
        return SOURCE_SVG_PATH
    if not DOWNLOAD_HTML_PATH.exists():
        raise FileNotFoundError(
            f"Missing source asset at {SOURCE_SVG_PATH} and download fallback at {DOWNLOAD_HTML_PATH}"
        )
    html = DOWNLOAD_HTML_PATH.read_text()
    match = re.search(r"(<svg\b.*?</svg>)", html, re.S)
    if not match:
        raise ValueError(f"Could not find inline SVG in {DOWNLOAD_HTML_PATH}")
    SOURCE_SVG_PATH.write_text(match.group(1))
    return SOURCE_SVG_PATH


def load_base_root() -> ET.Element:
    source_path = ensure_source_svg()
    source_root = ET.fromstring(source_path.read_text())
    scene = next((element for element in source_root.iter() if element.attrib.get("id") == "scene-group"), None)
    if scene is None:
        raise ValueError("Could not find scene-group in source SVG")

    root = ET.Element(svg_tag("svg"), {"viewBox": "120 120 320 170"})
    style = ET.SubElement(root, svg_tag("style"))
    style.text = COLOR_STYLE
    root.append(copy.deepcopy(scene))

    for removable in ("roar-text", "roar-lines", "blink"):
        remove_element_by_id(root, removable)
    for element in list(root.iter()):
        if element.attrib.get("class") == "dust-p":
            remove_element(root, element)
    tongue = find_by_id(root, "tongue")
    if tongue is not None:
        tongue.set("opacity", "0")
    return root


def find_by_id(root: ET.Element, element_id: str) -> ET.Element | None:
    return next((element for element in root.iter() if element.attrib.get("id") == element_id), None)


def remove_element(root: ET.Element, target: ET.Element) -> bool:
    for parent in root.iter():
        for child in list(parent):
            if child is target:
                parent.remove(child)
                return True
            if remove_element(child, target):
                return True
    return False


def remove_element_by_id(root: ET.Element, element_id: str) -> None:
    element = find_by_id(root, element_id)
    if element is not None:
        remove_element(root, element)


def apply_frame_spec(base_root: ET.Element, spec: FrameSpec) -> ET.Element:
    root = copy.deepcopy(base_root)
    for element_id, transform in spec.transforms.items():
        element = find_by_id(root, element_id)
        if element is None:
            raise ValueError(f"Missing SVG element id={element_id}")
        element.set("transform", transform)
    tongue = find_by_id(root, "tongue")
    if tongue is not None and spec.show_tongue:
        tongue.set("opacity", "1")
    if spec.hit_eye:
        pupil = next(
            (
                element
                for element in root.iter()
                if element.tag == svg_tag("circle")
                and element.attrib.get("class") == "dino-eye-p"
            ),
            None,
        )
        if pupil is not None:
            parent = find_parent(root, pupil)
            if parent is not None:
                parent.remove(pupil)
                for x1, y1, x2, y2 in ((371, 141, 380, 150), (380, 141, 371, 150)):
                    parent.append(
                        ET.Element(
                            svg_tag("line"),
                            {
                                "x1": str(x1),
                                "y1": str(y1),
                                "x2": str(x2),
                                "y2": str(y2),
                                "stroke": "#111111",
                                "stroke-width": "3",
                                "stroke-linecap": "round",
                            },
                        )
                    )
    return root


def find_parent(root: ET.Element, target: ET.Element) -> ET.Element | None:
    for parent in root.iter():
        for child in list(parent):
            if child is target:
                return parent
    return None


def render_darkness_grid(root: ET.Element) -> list[list[float]]:
    temp_svg = (REPO_ROOT / ".tmp_dino_frame.svg").resolve()
    try:
        ET.ElementTree(root).write(temp_svg, encoding="unicode")
        output = subprocess.run(
            [
                "magick",
                str(temp_svg),
                "-background",
                "none",
                "-resize",
                f"{RENDER_WIDTH}x{RENDER_HEIGHT}!",
                "txt:-",
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()[1:]
    finally:
        temp_svg.unlink(missing_ok=True)

    grid = [[0.0 for _ in range(RENDER_WIDTH)] for _ in range(RENDER_HEIGHT)]
    for line in output:
        position, color = line.split(":", 1)
        x, y = map(int, position.split(","))
        red, green, blue, alpha = [int(value) for value in color.split(")")[0].strip()[1:].split(",")[:4]]
        alpha_ratio = alpha / 65535.0
        luminance = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 65535.0
        grid[y][x] = alpha_ratio * (1.0 - luminance)
    return grid


def union_bbox(grids: list[list[list[float]]]) -> tuple[int, int, int, int]:
    left = RENDER_WIDTH
    right = 0
    top = RENDER_HEIGHT
    bottom = 0
    for grid in grids:
        for y, row in enumerate(grid):
            for x, value in enumerate(row):
                if value > 0.07:
                    left = min(left, x)
                    right = max(right, x)
                    top = min(top, y)
                    bottom = max(bottom, y)
    return left, right, top, bottom


def crop_grid(grid: list[list[float]], bbox: tuple[int, int, int, int]) -> list[list[float]]:
    left, right, top, bottom = bbox
    return [row[left : right + 1] for row in grid[top : bottom + 1]]


def resample_grid(grid: list[list[float]], target_width: int, target_height: int) -> list[list[float]]:
    source_height = len(grid)
    source_width = len(grid[0])
    output = [[0.0 for _ in range(target_width)] for _ in range(target_height)]
    for ty in range(target_height):
        source_y0 = ty * source_height / target_height
        source_y1 = (ty + 1) * source_height / target_height
        y_start = int(source_y0)
        y_end = min(source_height, int(source_y1 + 0.9999))
        for tx in range(target_width):
            source_x0 = tx * source_width / target_width
            source_x1 = (tx + 1) * source_width / target_width
            x_start = int(source_x0)
            x_end = min(source_width, int(source_x1 + 0.9999))
            total = 0.0
            count = 0
            for sy in range(y_start, y_end):
                for sx in range(x_start, x_end):
                    total += grid[sy][sx]
                    count += 1
            output[ty][tx] = total / count if count else 0.0
    return output


def grid_to_quadrants(grid: list[list[float]]) -> list[str]:
    quadrant_map = {
        0: " ",
        1: "▘",
        2: "▝",
        3: "▀",
        4: "▖",
        5: "▌",
        6: "▞",
        7: "▛",
        8: "▗",
        9: "▚",
        10: "▐",
        11: "▜",
        12: "▄",
        13: "▙",
        14: "▟",
        15: "█",
    }
    rows: list[str] = []
    height = len(grid)
    width = len(grid[0])
    for y in range(0, height, 2):
        line = []
        for x in range(0, width, 2):
            bits = 0
            for dy in range(2):
                for dx in range(2):
                    if y + dy < height and x + dx < width and grid[y + dy][x + dx] >= DARKNESS_THRESHOLD:
                        bits |= 1 << (dy * 2 + dx)
            line.append(quadrant_map[bits])
        rows.append("".join(line).rstrip())
    return rows


def frame_specs() -> dict[str, list[FrameSpec] | FrameSpec]:
    return {
        "idle": [
            FrameSpec(
                name="idle_1",
                transforms={
                    "idle-group": "translate(0 -1)",
                    "head-group": "rotate(2 340 175)",
                    "tail-base": "rotate(5 262 195)",
                    "tail-tip": "rotate(-8 195 186)",
                    "arm": "rotate(-4 340 190)",
                    "arm-back": "rotate(-2 330 190)",
                },
            ),
            FrameSpec(
                name="idle_2",
                transforms={
                    "head-group": "rotate(-1 340 175)",
                    "tail-base": "rotate(-4 262 195)",
                    "tail-tip": "rotate(2 195 186)",
                    "arm": "rotate(3 340 190)",
                    "arm-back": "rotate(2 330 190)",
                },
            ),
        ],
        "run": [
            FrameSpec(
                name="run_1",
                transforms={
                    "left-thigh": "rotate(15 295 220)",
                    "left-shin": "rotate(-15 293 244)",
                    "left-foot": "rotate(0 293 262)",
                    "right-thigh": "rotate(-5 320 220)",
                    "right-shin": "rotate(5 318 244)",
                    "right-foot": "rotate(10 318 262)",
                },
            ),
            FrameSpec(
                name="run_2",
                transforms={
                    "idle-group": "translate(1 -3)",
                    "head-group": "rotate(2 340 175)",
                    "tail-base": "rotate(10 262 195)",
                    "tail-tip": "rotate(-12 195 186)",
                    "arm": "rotate(-12 340 190)",
                    "arm-forearm": "rotate(15 350 208)",
                    "arm-back": "rotate(6 330 190)",
                    "left-thigh": "rotate(25 295 220)",
                    "left-shin": "rotate(-5 293 244)",
                    "left-foot": "rotate(-15 293 262)",
                    "right-thigh": "rotate(-20 320 220)",
                    "right-shin": "rotate(30 318 244)",
                    "right-foot": "rotate(5 318 262)",
                },
            ),
            FrameSpec(
                name="run_3",
                transforms={
                    "idle-group": "translate(0 -1)",
                    "head-group": "rotate(1 340 175)",
                    "tail-base": "rotate(4 262 195)",
                    "tail-tip": "rotate(-4 195 186)",
                    "arm": "rotate(-3 340 190)",
                    "arm-forearm": "rotate(5 350 208)",
                    "arm-back": "rotate(2 330 190)",
                    "left-thigh": "rotate(5 295 220)",
                    "left-shin": "rotate(6 293 244)",
                    "left-foot": "rotate(8 293 262)",
                    "right-thigh": "rotate(10 320 220)",
                    "right-shin": "rotate(-10 318 244)",
                    "right-foot": "rotate(0 318 262)",
                },
            ),
            FrameSpec(
                name="run_4",
                transforms={
                    "head-group": "rotate(0 340 175)",
                    "tail-base": "rotate(0 262 195)",
                    "tail-tip": "rotate(0 195 186)",
                    "arm": "rotate(1 340 190)",
                    "arm-forearm": "rotate(-2 350 208)",
                    "arm-back": "rotate(-1 330 190)",
                    "left-thigh": "rotate(-5 295 220)",
                    "left-shin": "rotate(5 293 244)",
                    "left-foot": "rotate(10 293 262)",
                    "right-thigh": "rotate(15 320 220)",
                    "right-shin": "rotate(-15 318 244)",
                    "right-foot": "rotate(0 318 262)",
                },
            ),
            FrameSpec(
                name="run_5",
                transforms={
                    "idle-group": "translate(1 -3)",
                    "head-group": "rotate(-1 340 175)",
                    "tail-base": "rotate(-8 262 195)",
                    "tail-tip": "rotate(-10 195 186)",
                    "arm": "rotate(8 340 190)",
                    "arm-forearm": "rotate(-5 350 208)",
                    "arm-back": "rotate(-8 330 190)",
                    "left-thigh": "rotate(-20 295 220)",
                    "left-shin": "rotate(30 293 244)",
                    "left-foot": "rotate(5 293 262)",
                    "right-thigh": "rotate(25 320 220)",
                    "right-shin": "rotate(-5 318 244)",
                    "right-foot": "rotate(-15 318 262)",
                },
            ),
            FrameSpec(
                name="run_6",
                transforms={
                    "idle-group": "translate(0 -1)",
                    "head-group": "rotate(1 340 175)",
                    "tail-base": "rotate(5 262 195)",
                    "tail-tip": "rotate(-6 195 186)",
                    "arm": "rotate(-6 340 190)",
                    "arm-forearm": "rotate(8 350 208)",
                    "arm-back": "rotate(4 330 190)",
                    "left-thigh": "rotate(8 295 220)",
                    "left-shin": "rotate(-5 293 244)",
                    "left-foot": "rotate(0 293 262)",
                    "right-thigh": "rotate(-2 320 220)",
                    "right-shin": "rotate(8 318 244)",
                    "right-foot": "rotate(8 318 262)",
                },
            ),
        ],
        "jump_up": FrameSpec(
            name="jump_up",
            transforms={
                "idle-group": "translate(0 -1)",
                "head-group": "rotate(2 340 175)",
                "tail-base": "rotate(6 262 195)",
                "tail-tip": "rotate(-8 195 186)",
                "left-thigh": "rotate(8 295 220)",
                "left-shin": "rotate(32 293 244)",
                "left-foot": "rotate(18 293 262)",
                "right-thigh": "rotate(12 320 220)",
                "right-shin": "rotate(18 318 244)",
                "right-foot": "rotate(10 318 262)",
            },
        ),
        "apex": FrameSpec(
            name="apex",
            transforms={
                "head-group": "rotate(1 340 175)",
                "tail-base": "rotate(2 262 195)",
                "tail-tip": "rotate(-4 195 186)",
                "left-thigh": "rotate(0 295 220)",
                "left-shin": "rotate(28 293 244)",
                "left-foot": "rotate(18 293 262)",
                "right-thigh": "rotate(0 320 220)",
                "right-shin": "rotate(28 318 244)",
                "right-foot": "rotate(18 318 262)",
            },
        ),
        "fall": FrameSpec(
            name="fall",
            transforms={
                "head-group": "rotate(-1 340 175)",
                "tail-base": "rotate(-4 262 195)",
                "tail-tip": "rotate(3 195 186)",
                "left-thigh": "rotate(-12 295 220)",
                "left-shin": "rotate(12 293 244)",
                "left-foot": "rotate(4 293 262)",
                "right-thigh": "rotate(14 320 220)",
                "right-shin": "rotate(-10 318 244)",
                "right-foot": "rotate(-6 318 262)",
            },
        ),
        "duck": [
            FrameSpec(
                name="duck_1",
                transforms={
                    "scene-group": "translate(-20 42) scale(1.12 0.72)",
                    "head-group": "rotate(-6 340 175)",
                    "tail-base": "rotate(6 262 195)",
                    "tail-tip": "rotate(-5 195 186)",
                },
            ),
            FrameSpec(
                name="duck_2",
                transforms={
                    "scene-group": "translate(-22 44) scale(1.14 0.7)",
                    "head-group": "rotate(-10 340 175)",
                    "jaw": "rotate(10 380 168)",
                    "tail-base": "rotate(8 262 195)",
                    "tail-tip": "rotate(-8 195 186)",
                },
                show_tongue=True,
            ),
        ],
        "hit": FrameSpec(
            name="hit",
            transforms={
                "head-group": "rotate(-7 340 175)",
                "jaw": "rotate(8 380 168)",
                "tail-base": "rotate(-10 262 195)",
                "tail-tip": "rotate(8 195 186)",
                "left-thigh": "rotate(10 295 220)",
                "left-shin": "rotate(10 293 244)",
                "right-thigh": "rotate(10 320 220)",
                "right-shin": "rotate(10 318 244)",
            },
            hit_eye=True,
        ),
        "roar": [
            FrameSpec(
                name="roar_1",
                transforms={
                    "idle-group": "translate(2 -3)",
                    "head-group": "rotate(-18 340 175)",
                    "jaw": "rotate(12 380 168)",
                    "arm": "rotate(-18 340 190)",
                    "arm-forearm": "rotate(24 350 208)",
                    "arm-back": "rotate(-12 330 190)",
                    "tail-base": "rotate(10 262 195)",
                    "tail-tip": "rotate(-15 195 186)",
                },
                show_tongue=True,
            ),
            FrameSpec(
                name="roar_2",
                transforms={
                    "idle-group": "translate(-1 -2)",
                    "head-group": "rotate(-18 340 175)",
                    "jaw": "rotate(22 380 168)",
                    "arm": "rotate(-30 340 190)",
                    "arm-forearm": "rotate(35 350 208)",
                    "arm-back": "rotate(-18 330 190)",
                    "tail-base": "rotate(-8 262 195)",
                    "tail-tip": "rotate(12 195 186)",
                },
                show_tongue=True,
            ),
            FrameSpec(
                name="roar_3",
                transforms={
                    "idle-group": "translate(1 -1)",
                    "head-group": "rotate(-5 340 175)",
                    "jaw": "rotate(10 380 168)",
                    "arm": "rotate(-10 340 190)",
                    "arm-forearm": "rotate(12 350 208)",
                    "arm-back": "rotate(-6 330 190)",
                    "tail-base": "rotate(8 262 195)",
                    "tail-tip": "rotate(-8 195 186)",
                },
                show_tongue=True,
            ),
        ],
    }


def render_frames() -> dict[str, list[str] | list[list[str]]]:
    base_root = load_base_root()
    specs = frame_specs()
    flat_specs: list[tuple[str, FrameSpec]] = []
    for state, state_specs in specs.items():
        if isinstance(state_specs, list):
            flat_specs.extend((state, spec) for spec in state_specs)
        else:
            flat_specs.append((state, state_specs))

    raw_grids = [(state, spec, render_darkness_grid(apply_frame_spec(base_root, spec))) for state, spec in flat_specs]
    bbox = union_bbox([grid for _, _, grid in raw_grids])

    output: dict[str, list[str] | list[list[str]]] = {}
    for state, spec, grid in raw_grids:
        cropped = crop_grid(grid, bbox)
        resized = resample_grid(cropped, TARGET_PIXEL_WIDTH, TARGET_PIXEL_HEIGHT)
        lines = grid_to_quadrants(resized)
        existing = output.get(state)
        if isinstance(specs[state], list):
            if existing is None:
                output[state] = [lines]
            else:
                assert isinstance(existing, list)
                existing.append(lines)
        else:
            output[state] = lines
    return output


def write_output(frames: dict[str, list[str] | list[list[str]]]) -> None:
    OUTPUT_PATH.write_text(
        "# Generated by scripts/generate_dino_svg_assets.py\n"
        "# Source: assets/source/dinosaur_svg_sprite_animation.svg\n\n"
        f"SVG_TYRANT_FRAMES = {repr(frames)}\n"
    )


def main() -> None:
    frames = render_frames()
    write_output(frames)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
