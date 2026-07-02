#!/usr/bin/env python3
"""Configuration file parsing and validation for the maze generator.

This module reads a simple ``KEY=VALUE`` configuration file, validates
every mandatory and optional setting, and returns a ``MazeConfig``
ready to be used by the rest of the program. Any invalid or missing
configuration causes a clear error message and a clean exit, instead
of letting the program crash with a raw traceback.
"""

import sys
from dataclasses import dataclass
from typing import Dict, Optional, List
from .write_maze import Coord


mandatory_keys = {'WIDTH', 'HEIGHT', 'ENTRY', 'EXIT', 'OUTPUT_FILE',
                  'PERFECT'}

COLOR_NAMES: Dict[str, int] = {
    "gray":    250,
    "white":   255,
    "black":   232,
    "red":     196,
    "orange":  214,
    "yellow":  226,
    "green":   46,
    "cyan":    51,
    "blue":    33,
    "purple":  93,
    "pink":    211,
    "magenta": 201,
}

WALL_PALETTE: List[int] = [250, 211, 120, 117]
PATH_PALETTE: List[int] = [33, 51, 226, 214, 211]
PATTERN_PALETTE: List[int] = [46, 226, 214, 196, 51]


@dataclass(frozen=True)
class MazeConfig:
    """Validated settings loaded from the configuration file."""

    width: int
    height: int
    entry: Coord
    exit: Coord
    output_file: str
    perfect: bool
    seed: Optional[int] = None
    algorithm: str = "backtracker"
    wall_color: int = 250
    path_color: int = 33
    pattern_color: int = 46


def get_coords(coord_str: str, w: int, h: int, key_name: str) -> Coord:
    """Parse and validate a "x,y" coordinate string.

    Args:
        coord_str: Raw value from the config file, expected as "x,y".
        w: Maze width, used to validate the x bound.
        h: Maze height, used to validate the y bound.
        key_name: Name of the config key (used in error messages).

    Returns:
        The parsed coordinate as a ``Coord``.

    Raises:
        ValueError: If the format is invalid or the coordinate falls
            outside the maze bounds.
    """

    parts = coord_str.split(',')
    if len(parts) != 2:
        raise ValueError(f"Format {key_name} invalid."
                         "Must be 'x,y'")
    x, y = int(parts[0].strip()), int(parts[1].strip())
    if not (0 <= x < w and 0 <= y < h):
        raise ValueError(f"{key_name} ({x},{y}) out of the maze size")
    return Coord(x, y)


def parse_color(value: str, key_name: str) -> int:
    """Parse and validate a color value from the configuration file.

    Accepts either a color name (e.g. ``"blue"``) from the built-in
    palette, or a raw ANSI 256-color integer (0-255).

    Args:
        value: Raw string value from the config file.
        key_name: Name of the config key (used in error messages).

    Returns:
        The ANSI 256-color code as an integer.

    Raises:
        ValueError: If the value is not a known name or a valid
            integer in the 0-255 range.
    """
    lower = value.lower().strip()
    if lower in COLOR_NAMES:
        return COLOR_NAMES[lower]
    try:
        code = int(lower)
    except ValueError:
        valid = ", ".join(sorted(COLOR_NAMES))
        raise ValueError(
            f"{key_name} '{value}' is not a known color name "
            f"(accepted: {valid}) and is not a valid integer."
        )
    if not (0 <= code <= 255):
        raise ValueError(
            f"{key_name} value {code} is out of the ANSI color range (0-255)."
        )
    return code


def load_config(file_path: str) -> MazeConfig:
    """Load, validate and return the maze configuration from a file.

    Reads ``KEY=VALUE`` lines (ignoring blank lines and ``#``
    comments), checks every mandatory key is present, and validates
    each value's type and range. On any error - missing file, bad
    syntax, missing key, or invalid value - prints a clear message to
    stderr and exits the program with status 1, instead of raising an
    unhandled exception.

    Args:
        file_path: Path to the configuration file.

    Returns:
        A fully validated ``MazeConfig``.
    """

    cfg_data: Dict[str, str] = {}
    allowed_keys = mandatory_keys | {
        'SEED', 'ALGORITHM',
        'WALL_COLOR', 'PATH_COLOR', 'PATTERN_COLOR'
        }

    try:
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                extracted_line = line.split('#', 1)[0].strip()
                if not extracted_line:
                    continue

                if '=' not in extracted_line:
                    raise ValueError(f"Line {line_num}: Format invalid. "
                                     "Missing '='")

                key, val = extracted_line.split('=', 1)
                clean_key = key.strip().upper()

                if clean_key not in allowed_keys:
                    continue

                new_value = val.strip()
                if clean_key in cfg_data:
                    print(
                        f"Warning: Line {line_num}: '{clean_key}' is "
                        f"defined more than once. Using '{new_value}' "
                        f"instead of '{cfg_data[clean_key]}'.",
                        file=sys.stderr,
                    )

                cfg_data[clean_key] = val.strip()

    except FileNotFoundError:
        print(f"Error: Configuration file '{file_path}' not found.",
              file=sys.stderr)
        sys.exit(1)
    except Exception as error:
        print(f"Error reading the file: {error}", file=sys.stderr)
        sys.exit(1)

    missing = mandatory_keys - cfg_data.keys()
    if missing:
        print(f"Error: Mandatory keys are missing: {', '.join(missing)}",
              file=sys.stderr)
        sys.exit(1)

    try:
        width = int(cfg_data['WIDTH'])
        height = int(cfg_data['HEIGHT'])
        if width <= 0 or height <= 0:
            raise ValueError("WIDTH and HEIGHT must be bigger than 0")
        if width > 1000 or height > 1000:
            raise ValueError("WIDTH and HEIGHT can't be higher than 1000")

        entry_coord = get_coords(cfg_data['ENTRY'], width, height, 'ENTRY')
        exit_coord = get_coords(cfg_data['EXIT'], width, height, 'EXIT')

        if entry_coord == exit_coord:
            raise ValueError("ENTRY and EXIT can't be identical.")

        perfect_str = cfg_data['PERFECT'].lower()
        if perfect_str == 'true':
            perfect = True
        elif perfect_str == 'false':
            perfect = False
        else:
            raise ValueError("PERFECT must be a boolean value.")

        output_file = cfg_data['OUTPUT_FILE']
        if not output_file:
            raise ValueError("OUTPUT_FILE can't be empty.")

        if 'SEED' in cfg_data:
            seed = int(cfg_data['SEED'])
        else:
            seed = None

        algorithm = cfg_data.get('ALGORITHM', "backtracker")

        wall_color = parse_color(
            cfg_data['WALL_COLOR'], 'WALL_COLOR'
        ) if 'WALL_COLOR' in cfg_data else 250

        path_color = parse_color(
            cfg_data['PATH_COLOR'], 'PATH_COLOR'
        ) if 'PATH_COLOR' in cfg_data else 33

        pattern_color = parse_color(
            cfg_data['PATTERN_COLOR'], 'PATTERN_COLOR'
        ) if 'PATTERN_COLOR' in cfg_data else 46

        return MazeConfig(
            width=width,
            height=height,
            entry=entry_coord,
            exit=exit_coord,
            output_file=output_file,
            perfect=perfect,
            seed=seed,
            algorithm=algorithm,
            wall_color=wall_color,
            path_color=path_color,
            pattern_color=pattern_color,
        )

    except ValueError as error1:
        print(f"Validation error on the cofiguration values: {error1}",
              file=sys.stderr)
        sys.exit(1)
