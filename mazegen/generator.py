#!/usr/bin/env python3
"""Maze generation algorithms and pathfinding logic.

This module contains the reusable ``MazeGenerator`` class: it builds
a ``Maze`` (see ``write_maze.py``) using a chosen algorithm, and can
compute the shortest path between any two cells once the maze exists.
"""

import random
from typing import Optional, List, Set, Tuple
from .write_maze import Maze, Coord


class MazeGenerator:
    """Generates a random maze and exposes pathfinding utilities."""

    def __init__(
            self, width: int, height: int, seed: Optional[int] = None) -> None:
        """Initialize the generator with dimensions and an optional seed.

        Args:
            width: Number of columns (cells) of the maze.
            height: Number of rows (cells) of the maze.
            seed: Optional seed for the random number generator, used
                to make maze generation reproducible. If None, the
                maze layout will differ on every run.
        """

        self.width = width
        self.height = height
        self.maze = Maze(width, height)

        if seed is not None:
            random.seed(seed)

    def generate(
        self,
        algorithm: str = "backtracker",
        start_coord: Optional[Coord] = None,
        perfect: bool = True
                ) -> Maze:
        """Build the maze grid using the requested algorithm.

        Args:
            algorithm: Either "backtracker" or "binary_tree". Any other
                value falls back to "backtracker".
            start_coord: Cell where generation starts (only used by the
                backtracker algorithm). Defaults to (0, 0).
            perfect: If True, the maze keeps exactly one path between
                any two cells (a perfect maze / spanning tree). If
                False, a few extra walls are randomly removed after
                generation to create loops (multiple possible paths).

        Returns:
            The generated Maze instance (same object as ``self.maze``).
        """

        if start_coord is None:
            start_coord = Coord(0, 0)
        elif isinstance(start_coord, tuple):
            start_coord = Coord(start_coord[0], start_coord[1])

        if algorithm.lower() == "binary_tree":
            self._generate_binary_tree()
        else:
            self._generate_backtracker(start_coord)

        self._enforce_corridor_width()

        if not perfect:
            self._add_loops()

        return self.maze

    def _get_unvisited_neighbors(
        self, coord: Coord
            ) -> List[Tuple[Coord, str]]:
        """Find unvisited, non-42 neighbors of a cell.

        Used by the Recursive Backtracker to know where it can still
        carve a new passage from the current cell.

        Args:
            coord: Cell whose neighbors are checked.

        Returns:
            List of (neighbor_coordinate, direction_from_current)
            tuples for each unvisited, non-42 neighbor.
        """

        neighbors = []
        directions = [
            (-1, 0, "north"),
            (1, 0, "south"),
            (0, 1, "east"),
            (0, -1, "west")
        ]

        for dy, dx, direction in directions:
            ny, nx = coord.y + dy, coord.x + dx

            if 0 <= ny < self.height and 0 <= nx < self.width:
                neighbor_cell = self.maze.grid[ny][nx]

                if not neighbor_cell.visited and not neighbor_cell.is_42:
                    neighbors.append((Coord(nx, ny), direction))

        return neighbors

    def _generate_backtracker(self, start_coord: Coord) -> None:
        """Generate a perfect maze using an iterative Recursive Backtracker.

        Starting from ``start_coord``, repeatedly moves to a random
        unvisited neighbor and opens the wall towards it, pushing the
        previous cell on a stack. When a cell has no unvisited
        neighbor left, it backtracks by popping the stack. This always
        produces a spanning tree (a perfect maze: exactly one path
        between any two cells), and never visits 42-pattern cells.

        Args:
            start_coord: Cell where the carving begins.
        """

        stack: List[Coord] = []
        current = start_coord

        self.maze.grid[current.y][current.x].visited = True

        while True:
            neighbors = self._get_unvisited_neighbors(current)

            if neighbors:
                next_coord, direction = random.choice(neighbors)

                stack.append(current)
                self.maze.open_walls(current, direction)

                current = next_coord
                self.maze.grid[current.y][current.x].visited = True

            elif stack:
                current = stack.pop()

            else:
                break

    def _generate_binary_tree(self) -> None:
        """Generate a maze using the Binary Tree algorithm (Bonus).

        For each cell, scanned row by row, a wall is opened towards
        north or east (the classic Binary Tree rule), which is enough
        to guarantee connectivity in a normal grid because cell (0, 0)
        always ends up reachable through a chain of north/east links.

        The 42 pattern breaks that guarantee: a cell can have both its
        north and east neighbors blocked, and a naive south/west
        fallback may connect it to a neighbor that itself is not (yet)
        connected to the rest of the maze. To stay correct, we track
        which cells are already connected to the starting cell's
        component and only fall back to a neighbor that is part of
        that component. Any cell that still cannot connect after
        scanning the whole grid is retried in extra passes against
        the now-larger connected component, until everything is
        attached or no more progress can be made.
        """

        pending = [
            Coord(x, y)
            for y in range(self.height)
            for x in range(self.width)
            if not self.maze.grid[y][x].is_42
        ]
        if not pending:
            return

        seed_cell = random.choice(pending)
        connected: Set[Coord] = {seed_cell}
        pending = [c for c in pending if c != seed_cell]

        progress = True
        while pending and progress:
            progress = False
            still_pending = []
            random.shuffle(pending)

            for coord in pending:
                if self._connect_cell_binary_tree(coord, connected):
                    connected.add(coord)
                    progress = True
                else:
                    still_pending.append(coord)

            pending = still_pending

    def _connect_cell_binary_tree(
        self, coord: Coord, connected: Set[Coord]
    ) -> bool:
        """Try to connect one cell to the existing connected component.

        Prefers the classic north/east directions; falls back to
        south/west only towards a neighbor that is already part of
        ``connected``, so the resulting structure is always one
        single connected component (no isolated cells).

        Args:
            coord: Cell to connect.
            connected: Set of coordinates already connected to the
                maze's starting cell. Mutated by the caller, not here.

        Returns:
            True if the cell was successfully connected this round.
        """
        x, y = coord.x, coord.y
        candidates = []

        if y > 0 and not self.maze.grid[y - 1][x].is_42:
            candidates.append((Coord(x, y - 1), "north"))
        if x < self.width - 1 and not self.maze.grid[y][x + 1].is_42:
            candidates.append((Coord(x + 1, y), "east"))
        if y < self.height - 1 and not self.maze.grid[y + 1][x].is_42:
            candidates.append((Coord(x, y + 1), "south"))
        if x > 0 and not self.maze.grid[y][x - 1].is_42:
            candidates.append((Coord(x - 1, y), "west"))

        connected_candidates = [
            (neighbor, direction)
            for neighbor, direction in candidates
            if neighbor in connected
        ]
        if not connected_candidates:
            return False

        # Prefer north/east when available, to keep the classic
        # Binary Tree look; otherwise use whichever connected
        # neighbor is available (south/west fallback).
        preferred = [
            pair
            for pair in connected_candidates
            if pair[1] in ("north", "east")
        ]
        neighbor, direction = random.choice(preferred or connected_candidates)
        self.maze.open_walls(coord, direction)
        return True

    def _enforce_corridor_width(self) -> None:
        """Break up every fully-open 3x3 (or larger) area in the maze.

        The subject forbids corridors/open areas wider than 2 cells:
        a 2x3 or 3x2 open room is fine, but a 3x3 fully-open room is
        not. A block is considered "open" only when every wall
        between two of its adjacent cells is missing - a real open
        room, not just a winding corridor that happens to visit all
        9 cells one at a time (which is normal and legal, even in a
        perfect maze). This scans every possible 3x3 block of cells;
        whenever a block has no internal walls at all, one of its
        internal walls is closed to split it back into smaller
        (legal) open areas. The scan repeats until no 3x3 open block
        remains, since closing one wall can still leave a
        neighboring 3x3 block fully open.
        """

        while True:
            block = self._find_open_3x3_block()
            if block is None:
                break
            self._split_block(block)

    def _find_open_3x3_block(self) -> Optional[Tuple[int, int]]:
        """Find the top-left corner of one fully-open 3x3 block, if any.

        Returns:
            The (x, y) coordinate of the block's top-left cell, or
            None if no fully-open 3x3 block exists in the maze.
        """
        for y in range(self.height - 2):
            for x in range(self.width - 2):
                cells = [
                    (yy, xx)
                    for yy in range(y, y + 3)
                    for xx in range(x, x + 3)
                ]
                if any(self.maze.grid[yy][xx].is_42 for yy, xx in cells):
                    continue
                if self._block_has_no_internal_walls(cells):
                    return (x, y)
        return None

    def _block_has_no_internal_walls(
        self, cells: List[Tuple[int, int]]
    ) -> bool:
        """Check if a block of cells forms one room with no inner walls.

        Unlike plain reachability (which a perfect maze's winding
        corridors can satisfy without forming a real room, since a
        path may simply pass through all 9 cells one at a time), this
        requires every wall between two cells that are both in
        ``cells`` to be open. That is the strict definition of an
        open area: a real fully-open room, not just a reachable group
        of cells.

        Args:
            cells: List of (y, x) coordinates forming the block.

        Returns:
            True if all internal walls of the block are open.
        """
        cell_set = set(cells)

        for cy, cx in cells:
            cell = self.maze.grid[cy][cx]
            if (cy, cx + 1) in cell_set and cell.east:
                return False
            if (cy + 1, cx) in cell_set and cell.south:
                return False

        return True

    def _split_block(self, block: Tuple[int, int]) -> None:
        """Close one internal wall of a 3x3 block to break it up.

        Closing the wall between the block's center cell and one of
        its 4 neighbors inside the block is enough to remove the
        fully-open 3x3 area while keeping the rest of the maze intact.

        Args:
            block: (x, y) coordinate of the block's top-left cell.
        """
        x, y = block
        center = Coord(x + 1, y + 1)
        direction = random.choice(["north", "south", "east", "west"])
        self._close_wall(center, direction)

    def _close_wall(self, coord: Coord, direction: str) -> None:
        """Close the wall of ``coord`` in ``direction`` and its neighbor.

        This is the exact opposite of ``Maze.open_walls``: it restores
        a wall on both sides to keep the maze data coherent.

        Args:
            coord: Coordinate of the cell whose wall is closed.
            direction: One of "north", "south", "east", "west".
        """
        opposite = {
            "north": "south",
            "south": "north",
            "east": "west",
            "west": "east",
        }
        move = {
            "north": (-1, 0),
            "south": (1, 0),
            "east": (0, 1),
            "west": (0, -1),
        }

        if direction not in opposite:
            return
        dy, dx = move[direction]
        ny, nx = coord.y + dy, coord.x + dx

        if not (0 <= ny < self.height and 0 <= nx < self.width):
            return

        setattr(self.maze.grid[coord.y][coord.x], direction, True)
        setattr(self.maze.grid[ny][nx], opposite[direction], True)

    def _add_loops(self, extra_wall_ratio: float = 0.08) -> None:
        """Randomly open a few extra walls to create loops in the maze.

        Used when PERFECT is False: starting from a perfect maze
        (single path between any two cells), this opens a small
        fraction of the remaining closed internal walls, creating
        cycles so that more than one path can exist between cells.

        Args:
            extra_wall_ratio: Fraction (0-1) of the closed internal
                walls to open. Kept small to preserve a maze-like
                structure rather than turning it into an open field.
        """
        closed_walls: List[Tuple[Coord, str]] = []

        for y in range(self.height):
            for x in range(self.width):
                cell = self.maze.grid[y][x]
                if cell.is_42:
                    continue
                if (
                    cell.east
                    and x < self.width - 1
                    and not self.maze.grid[y][x + 1].is_42
                ):
                    closed_walls.append((Coord(x, y), "east"))
                if (
                    cell.south
                    and y < self.height - 1
                    and not self.maze.grid[y + 1][x].is_42
                ):
                    closed_walls.append((Coord(x, y), "south"))

        random.shuffle(closed_walls)
        target_opened = max(1, int(len(closed_walls) * extra_wall_ratio))
        target_opened = min(target_opened, len(closed_walls))

        opened = 0
        for coord, direction in closed_walls:
            if opened >= target_opened:
                break
            if self._would_break_corridor_rule(coord, direction):
                continue
            self.maze.open_walls(coord, direction)
            opened += 1

    def _would_break_corridor_rule(self, coord: Coord, direction: str) -> bool:
        """Check if opening this wall would create an open 2x2 block.

        Args:
            coord: Coordinate of the cell whose wall would open.
            direction: Direction of the wall to test ("east" or
                "south").

        Returns:
            True if opening this wall would create a fully-open 2x2
            block (and therefore break the max-corridor-width rule).
        """
        candidates = [(coord.x, coord.y)]
        if direction == "east":
            candidates.append((coord.x - 1, coord.y))
        else:
            candidates.append((coord.x, coord.y - 1))

        for x, y in candidates:
            if 0 <= x < self.width - 1 and 0 <= y < self.height - 1:
                if self._would_2x2_be_open(x, y, coord, direction):
                    return True
        return False

    def _would_2x2_be_open(
        self, x: int, y: int, opened_coord: Coord, opened_direction: str
    ) -> bool:
        """Simulate opening one wall and check if a 2x2 block becomes open.

        Args:
            x: Column of the top-left cell of the 2x2 block to test.
            y: Row of the top-left cell of the 2x2 block to test.
            opened_coord: Cell whose wall is hypothetically opened.
            opened_direction: Direction of the hypothetical opening.

        Returns:
            True if, after the hypothetical wall removal, the 2x2
            block starting at (x, y) would be fully open.
        """
        walls = {
            "top_east": self.maze.grid[y][x].east,
            "top_south": self.maze.grid[y][x].south,
            "right_south": self.maze.grid[y][x + 1].south,
            "left_east": self.maze.grid[y + 1][x].east,
        }

        if opened_coord == Coord(x, y) and opened_direction == "east":
            walls["top_east"] = False
        if opened_coord == Coord(x, y) and opened_direction == "south":
            walls["top_south"] = False
        if opened_coord == Coord(x + 1, y) and opened_direction == "south":
            walls["right_south"] = False
        if opened_coord == Coord(x, y + 1) and opened_direction == "east":
            walls["left_east"] = False

        return not any(walls.values())

    def solve(self, start: Coord, end: Coord) -> str:
        """Find the shortest path between two cells using BFS.

        Args:
            start: Coordinate of the starting cell.
            end: Coordinate of the target cell.

        Returns:
            A string of directions ("N", "S", "E", "W") describing the
            shortest path from ``start`` to ``end``, or an empty
            string if no path exists between them.
        """

        if isinstance(start, tuple):
            start = Coord(start[0], start[1])
        if isinstance(end, tuple):
            end = Coord(end[0], end[1])

        queue = [(start, "")]
        visited = {start}

        moves = [
            (-1, 0, "N", "north"),
            (1, 0, "S", "south"),
            (0, 1, "E", "east"),
            (0, -1, "W", "west")
        ]

        while queue:
            current, path = queue.pop(0)

            if current == end:
                return path

            cell = self.maze.grid[current.y][current.x]

            for dy, dx, letter, wall_name in moves:
                if not getattr(cell, wall_name):
                    ny, nx = current.y + dy, current.x + dx
                    next_coord = Coord(nx, ny)

                    if 0 <= ny < self.height and 0 <= nx < self.width:
                        if next_coord not in visited:
                            visited.add(next_coord)
                            queue.append((next_coord, path + letter))

        return ""

    def get_path_coords(self, start: Coord, path_str: str) -> List[Coord]:
        """Convert a path string (N/S/E/W letters) into coordinates.

    Args:
        start: Coordinate where the path begins. A plain
            ``(x, y)`` tuple is also accepted, for consistency
            with ``solve``.
        path_str: Directions string as returned by ``solve``.

    Returns:
        List of coordinates visited along the path, starting
        with ``start`` and ending at the final cell reached.
    """

        if isinstance(start, tuple) and not isinstance(start, Coord):
            start = Coord(start[0], start[1])

        coords = [start]
        curr_x, curr_y = start.x, start.y

        moves = {
            "N": (0, -1),
            "S": (0, 1),
            "E": (1, 0),
            "W": (-1, 0)
        }

        for letter in path_str:
            if letter in moves:
                dx, dy = moves[letter]
                curr_x += dx
                curr_y += dy
                coords.append(Coord(curr_x, curr_y))

        return coords
