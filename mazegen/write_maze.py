#!/usr/bin/env python3

from typing import NamedTuple, Tuple, Set, List, Optional


class Coord(NamedTuple):
    """A simple (x, y) coordinate pair.

    Using a NamedTuple makes coordinates immutable and hashable,
    so they can be stored in sets/dicts (e.g. to represent a path).
    """

    x: int
    y: int


class Cell:
    """A single cell of the maze grid.

    Every cell starts fully closed (all four walls present) and
    unvisited. Walls are opened later by the generator algorithms.
    """

    def __init__(self) -> None:
        """Initialize a closed, unvisited, non-42 cell."""

        self.north = True
        self.south = True
        self.east = True
        self.west = True
        self.visited = False
        self.is_42 = False


class Maze:
    """The maze grid: a 2D array of Cell objects plus rendering logic."""

    def __init__(self, width: int, height: int) -> None:
        """Create an empty (fully walled) maze and draw the 42 pattern.

        Args:
            width: Number of columns (cells) of the maze.
            height: Number of rows (cells) of the maze.
        """

        self.m_width: int = width
        self.m_height: int = height
        self.error_message: Optional[str] = None
        self.grid = [[Cell() for _ in range(width)] for _ in range(height)]

        self._apply_42_pattern()

    def _apply_42_pattern(self) -> None:
        """Mark the cells that draw a "42" shape in the maze center.

        The pattern is only applied if the maze is large enough AND
        the resulting non-42 cells still form a single connected
        region (ignoring walls, just cell adjacency). On very narrow
        mazes the pattern can otherwise physically split the grid into
        separate islands that no algorithm could ever reconnect. In
        either failure case, the pattern is skipped and an explanatory
        message is stored in ``self.error_message`` instead of
        raising an exception.
        """

        p42 = [
            [1, 0, 0, 0, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 0, 1, 1, 1],
            [0, 0, 1, 0, 1, 0, 0],
            [0, 0, 1, 0, 1, 1, 1]
        ]
        p42_h = 5
        p42_w = 7

        if self.m_height < p42_h or self.m_width < p42_w:
            self.error_message = (
                "Error: The size of the Maze is not big "
                "enough to fit the 42 logo pattern"
            )
            return

        # Center the pattern
        start_y = (self.m_height - p42_h) // 2
        start_x = (self.m_width - p42_w) // 2

        pattern_cells = {
            (start_y + y, start_x + x)
            for y in range(p42_h)
            for x in range(p42_w)
            if p42[y][x] == 1
        }

        if not self._stays_connected_without(pattern_cells):
            self.error_message = (
                "Error: The size of the Maze is too narrow to fit "
                "the 42 logo pattern without splitting the maze"
            )
            return

        for cell_y, cell_x in pattern_cells:
            self.grid[cell_y][cell_x].is_42 = True

    def _stays_connected_without(
        self, blocked: Set[Tuple[int, int]]
    ) -> bool:
        """Check that all non-blocked cells stay reachable from one another.

        This only looks at grid adjacency (ignoring walls), to verify
        that removing ``blocked`` cells from the grid would not split
        the remaining cells into separate, unreachable islands.

        Args:
            blocked: Set of (y, x) coordinates to treat as removed.

        Returns:
            True if every non-blocked cell can reach every other
            non-blocked cell through a chain of free neighbors.
        """
        all_cells = {
            (y, x)
            for y in range(self.m_height)
            for x in range(self.m_width)
        }
        free_cells = all_cells - blocked
        if not free_cells:
            return True

        start = next(iter(free_cells))
        to_visit = [start]
        seen = {start}

        while to_visit:
            cy, cx = to_visit.pop()
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (cy + dy, cx + dx)
                if neighbor in free_cells and neighbor not in seen:
                    seen.add(neighbor)
                    to_visit.append(neighbor)

        return len(seen) == len(free_cells)

    def is_cell_42(self, x: int, y: int) -> bool:
        """Return True if the cell at (x, y) belongs to the 42 pattern."""
        return self.grid[y][x].is_42

    def print_maze(
        self,
        path_coords: Optional[List[Coord]] = None,
        wall_color: str = "\033[0m",
        entry_coord: Optional[Coord] = None,
        exit_coord: Optional[Coord] = None,
        path_color: int = 33,
        pattern_color: int = 46,
    ) -> None:
        """Print the maze to the terminal using ANSI colors.

        Args:
            path_coords: Coordinates of the solution path to highlight,
                or None to draw the maze without any path.
            wall_color: ANSI foreground color escape code used to
                derive the background color of the walls.
            entry_coord: Coordinate of the entry cell, drawn in green.
            exit_coord: Coordinate of the exit cell, drawn in red.
            path_color: ANSI 256-color code for the solution path.
            pattern_color: ANSI 256-color code for the '42' pattern
                cells.
        """
        # ANSI COLORS
        RESET = "\033[0m"
        GREEN_BG = f"\033[48;5;{pattern_color}m"
        BLUE_BG = f"\033[48;5;{path_color}m"
        PATH_BG = "\033[48;5;236m"

        if "38;5;" in wall_color:
            bg_wall_color = wall_color.replace("38;5;", "48;5;")
        else:
            bg_wall_color = "\033[48;5;250m"

        W = f"{bg_wall_color} {RESET}"
        W3 = f"{bg_wall_color}   {RESET}"

        # Top boundary line
        top_line = ""
        for x in range(self.m_width):
            top_line += W + W3
        print(top_line + W)

        for y in range(self.m_height):
            mid_line = ""   # EAST/WEST Walls
            bot_line = ""   # SOUTH and corners

            for x in range(self.m_width):
                cell = self.grid[y][x]
                c_coord = Coord(x, y)

                is_path = path_coords and c_coord in path_coords

                if cell.west:
                    mid_line += W
                else:
                    # PAINT 42 CELLS BACKGROUND
                    if cell.is_42 or (x > 0 and self.grid[y][x - 1].is_42):
                        mid_line += f"{GREEN_BG} {RESET}"
                    elif is_path and (
                        x > 0 and path_coords and (
                                Coord(x - 1, y)) in path_coords
                                    ):
                        mid_line += f"{BLUE_BG} {RESET}"
                    else:
                        mid_line += f"{PATH_BG} {RESET}"

                if c_coord == entry_coord:
                    mid_line += f"\033[48;5;46m   {RESET}"
                elif c_coord == exit_coord:
                    mid_line += f"\033[48;5;196m   {RESET}"
                elif cell.is_42:
                    mid_line += f"{GREEN_BG}   {RESET}"
                elif is_path:
                    mid_line += f"{BLUE_BG}   {RESET}"
                else:
                    mid_line += f"{PATH_BG}   {RESET}"

                if cell.south:
                    bot_line += W + W3
                else:
                    if cell.is_42 or (y < self.m_height - 1
                                      and self.grid[y + 1][x].is_42):
                        bot_line += f"{W}{GREEN_BG}   {RESET}"
                    elif is_path and (path_coords
                                      and Coord(x, y + 1) in path_coords):
                        bot_line += f"{W}{BLUE_BG}   {RESET}"
                    else:
                        bot_line += f"{W}{PATH_BG}   {RESET}"

            if self.grid[y][-1].east:
                mid_line += W
            else:
                if self.grid[y][-1].is_42:
                    mid_line += f"{GREEN_BG} {RESET}"
                elif path_coords and Coord(self.m_width - 1, y) in path_coords:
                    mid_line += f"{BLUE_BG} {RESET}"
                else:
                    mid_line += f"{PATH_BG} {RESET}"

            # Bottom right corner
            bot_line += W

            # Print current line
            print(mid_line)
            print(bot_line)

    def open_walls(self, coord: Coord, direction: str) -> None:
        """Open the wall of ``coord`` in ``direction`` and its neighbor.

        Breaking a wall must stay coherent on both sides: if the east
        wall of a cell opens, the west wall of its eastern neighbor
        must open too. This method takes care of updating both cells
        and silently does nothing if the move would go out of bounds
        or the direction is invalid.

        Args:
            coord: Coordinate of the cell whose wall is opened.
            direction: One of "north", "south", "east", "west".
        """
        opposite = {
            "north": "south",
            "south": "north",
            "east": "west",
            "west": "east"
        }

        move = {
            "north": (-1, 0),
            "south": (1, 0),
            "east":  (0, 1),
            "west":  (0, -1)
        }

        if direction not in opposite:
            return
        dy, dx = move[direction]
        ny, nx = coord.y + dy, coord.x + dx

        if not (0 <= ny < self.m_height and 0 <= nx < self.m_width):
            return

        current_cell = self.grid[coord.y][coord.x]
        neighbor_cell = self.grid[ny][nx]

        # Open the wall on the current cell's side.
        setattr(current_cell, direction, False)
        # Open the matching wall on the neighbor's side.
        setattr(neighbor_cell, opposite[direction], False)
