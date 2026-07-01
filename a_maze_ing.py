#!/usr/bin/env python3
"""Entry point of the A-Maze-ing program.

Loads a configuration file, generates the maze, writes it to the
output file in the required hexadecimal format, and then opens an
interactive terminal menu to regenerate, solve, or recolor the maze.
"""

import time
import sys
from typing import List
from mazegen.parser import load_config, MazeConfig
from mazegen.generator import MazeGenerator


def write_output_file(
    file_path: str, generator: MazeGenerator, cfg: MazeConfig
) -> None:
    """Write the generated maze to the output file in hex format.

    The file contains, in order: one hexadecimal digit per cell
    (one row per line, encoding which of the 4 walls are closed),
    a blank line, the entry coordinates, the exit coordinates, and
    the shortest solution path as a string of N/S/E/W letters.

    Args:
        file_path: Path of the output file to write.
        generator: Generator holding the maze to export.
        cfg: Configuration providing the entry/exit coordinates.
    """

    grid_height = len(generator.maze.grid)
    grid_width = len(generator.maze.grid[0])

    with open(file_path, "w") as f:
        for y in range(grid_height):
            hex_line = ""
            for x in range(grid_width):
                cell = generator.maze.grid[y][x]
                val = 0
                if cell.north:
                    val |= 1
                if cell.east:
                    val |= 2
                if cell.south:
                    val |= 4
                if cell.west:
                    val |= 8

                hex_line += f"{val:X}"
            f.write(hex_line + "\n")

        f.write("\n")
        f.write(f"{cfg.entry.x},{cfg.entry.y}\n")
        f.write(f"{cfg.exit.x},{cfg.exit.y}\n")

        path_str = generator.solve(cfg.entry, cfg.exit)
        f.write(path_str + "\n")


def display_menu() -> None:
    """Prints the user interaction menu to the terminal."""
    print("\n" + "=" * 10 + " A-Maze-ing " + "=" * 10)
    print("1. Re-generate a new maze")
    print("2. Show/Hide path from entry to exit")
    print("3. Rotate wall color")
    print("4. Rotate path color")
    print("5. Rotate pattern (42) color")
    print("6. Quit")


def main() -> None:
    """Main program execution."""

    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]
    cfg = load_config(config_path)

    gen = MazeGenerator(cfg.width, cfg.height, cfg.seed)

    if (
        gen.maze.is_cell_42(cfg.entry.x, cfg.entry.y)
        or gen.maze.is_cell_42(cfg.exit.x, cfg.exit.y)
    ):
        print(
            "Error: ENTRY or EXIT coordinates fall inside the 42 pattern!",
            file=sys.stderr,
        )
        sys.exit(1)

    gen.generate(
        algorithm=cfg.algorithm,
        start_coord=cfg.entry,
        perfect=cfg.perfect,
    )
    write_output_file(cfg.output_file, gen, cfg)

    show_path = False
    current_wall_idx = 0
    current_path_idx = 0
    current_pattern_idx = 0

    from mazegen.parser import (
        WALL_PALETTE, PATH_PALETTE, PATTERN_PALETTE
    )

    def make_palette(base: List[int], start: int) -> List[int]:
        """Return a palette that begins with ``start``.

        If ``start`` is already the first element, the base palette is
        returned unchanged. Otherwise ``start`` is prepended so the
        program opens with exactly the color the user configured.
        """
        if base and base[0] == start:
            return base
        if start in base:
            idx = base.index(start)
            return base[idx:] + base[:idx]
        return [start] + base

    wall_palette = make_palette(WALL_PALETTE, cfg.wall_color)
    path_palette = make_palette(PATH_PALETTE, cfg.path_color)
    pattern_palette = make_palette(PATTERN_PALETTE, cfg.pattern_color)

    current_wall_idx = 0
    current_path_idx = 0
    current_pattern_idx = 0

    while True:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

        start_coord = cfg.entry
        end_coord = cfg.exit

        wall_ansi = f"\033[38;5;{wall_palette[current_wall_idx]}m"
        path_code = path_palette[current_path_idx]
        pattern_code = pattern_palette[current_pattern_idx]

        p_coords = None
        if show_path:
            raw_path = gen.solve(start_coord, end_coord)
            p_coords = gen.get_path_coords(start_coord, raw_path)

        if gen.maze.error_message:
            print(gen.maze.error_message, file=sys.stderr)
            gen.maze.error_message = None

        gen.maze.print_maze(
            path_coords=p_coords,
            wall_color=wall_ansi,
            entry_coord=cfg.entry,
            exit_coord=cfg.exit,
            path_color=path_code,
            pattern_color=pattern_code,
        )

        display_menu()

        try:
            choice = input("Choice? (1-6): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

        if choice == "1":
            gen = MazeGenerator(cfg.width, cfg.height, None)
            gen.generate(
                algorithm=cfg.algorithm,
                start_coord=cfg.entry,
                perfect=cfg.perfect,
                )
            write_output_file(cfg.output_file, gen, cfg)
            print("\n[!] New maze generated successfully.")

        elif choice == "2":
            if not show_path:
                show_path = True
                raw_path = gen.solve(start_coord, end_coord)
                full_path = gen.get_path_coords(start_coord, raw_path)

                print("[!] Solving maze...")
                sys.stdout.write("\033[?25l")
                sys.stdout.flush()

                for i in range(1, len(full_path) + 1):
                    sys.stdout.write("\033[H\033[J")
                    sys.stdout.flush()

                    partial_path = full_path[:i]
                    gen.maze.print_maze(
                        path_coords=partial_path,
                        wall_color=wall_ansi,
                        entry_coord=start_coord,
                        exit_coord=end_coord,
                        path_color=path_code,
                        pattern_color=pattern_code,
                    )
                    time.sleep(0.04)

                sys.stdout.write("\033[?25h")
                sys.stdout.write("\033[H\033[J")
                sys.stdout.flush()
            else:
                show_path = False
                sys.stdout.write("\033[H\033[J")
                sys.stdout.flush()

        elif choice == "3":
            current_wall_idx = (current_wall_idx + 1) % len(wall_palette)
            print("\n[!] Wall color rotated.")

        elif choice == "4":
            current_path_idx = (current_path_idx + 1) % len(path_palette)
            print("\n[!] Path color rotated.")

        elif choice == "5":
            current_pattern_idx = (
                (current_pattern_idx + 1) % len(pattern_palette)
            )
            print("\n[!] Pattern (42) color rotated.")

        elif choice == "6":
            print("\nGoodbye! :)")
            break
        else:
            print("\n[Invalid choice] Please enter a number between 1 and 6.")


if __name__ == "__main__":
    main()
