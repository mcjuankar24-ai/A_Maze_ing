*This project has been created as part of the 42 curriculum by lcristur, jmesa-ci.*

# 📚 A-Maze-ing

## 📝 Description

**A-Maze-ing** is a Python maze generator and solver. Given a configuration file, it generates a maze on a rectangular grid, draws a recognizable "42" pattern in its center, writes the maze to a file using a compact hexadecimal wall encoding, and displays it interactively in the terminal. The display lets you regenerate the maze, show or hide the shortest path between the entry and the exit, and independently cycle through colors for the walls, the solution path, and the "42" pattern.

The maze generation logic itself lives in a separate, reusable package (`mazegen`, see below) so it can be imported and reused in other projects without depending on the terminal display or the configuration file format.

## ⚙️ Instructions

### Installation

```bash
make install
```
This installs the development dependencies listed in `requirements.txt` (`flake8`, `mypy`, `build`).

### Running the program
```bash
make run
```

or directly:

```bash
python3 a_maze_ing.py config.txt
```
`config.txt` is the only argument and can be replaced with the path to any valid configuration file (see format below). A default `config.txt` is provided at the root of the repository.

### Other Makefile rules

| Rule | Description |
|---|---|
| `make install` | Install development dependencies. |
| `make run` | Run the program with `config.txt`. |
| `make debug` | Run the program under `pdb`. |
| `make clean` | Remove caches and build artifacts. |
| `make lint` | Run `flake8` and `mypy` with the required flags. |
| `make lint-strict` | Run `flake8` and `mypy --strict`. |

## Configuration file format
 
The configuration file contains one `KEY=VALUE` pair per line. Lines
starting with `#` are comments and are ignored.
 
| Key | Mandatory | Description | Example |
|---|---|---|---|
| `WIDTH` | yes | Maze width, in cells | `WIDTH=20` |
| `HEIGHT` | yes | Maze height, in cells | `HEIGHT=15` |
| `ENTRY` | yes | Entry coordinates `x,y` | `ENTRY=0,0` |
| `EXIT` | yes | Exit coordinates `x,y` | `EXIT=19,14` |
| `OUTPUT_FILE` | yes | Path of the generated output file | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | yes | `True` for a single-path maze, `False` to allow loops | `PERFECT=True` |
| `SEED` | no | Integer seed for reproducible generation | `SEED=42` |
| `ALGORITHM` | no | `backtracker` (default) or `binary_tree` | `ALGORITHM=backtracker` |
| `WALL_COLOR` | no | Starting color for the maze walls | `WALL_COLOR=gray` |
| `PATH_COLOR` | no | Starting color for the solution path | `PATH_COLOR=blue` |
| `PATTERN_COLOR` | no | Starting color for the "42" pattern cells | `PATTERN_COLOR=green` |

The three color keys accept either a color name or a raw ANSI
256-color integer (0-255). 

| Name | `WALL_COLOR` | `PATH_COLOR` | `PATTERN_COLOR` |
|---|---|---|---|
| `black` | ✓ | ✓ | ✓ |
| `blue` | ✓ | ✓ (default) | ✓ |
| `cyan` | ✓ | ✓ | ✓ |
| `gray` | ✓ (default) | ✓ | ✓ |
| `green` | ✓ | ✓ | ✓ (default) |
| `magenta` | ✓ | ✓ | ✓ |
| `orange` | ✓ | ✓ | ✓ |
| `pink` | ✓ | ✓ | ✓ |
| `purple` | ✓ | ✓ | ✓ |
| `red` | ✓ | ✓ | ✓ |
| `white` | ✓ | ✓ | ✓ |
| `yellow` | ✓ | ✓ | ✓ |
 
All 12 names are accepted for all three keys. If a key is omitted, the
program uses its default (shown above). An invalid name causes a clear
error message listing the accepted values.
 
Example (the default `config.txt`):
 
```
WIDTH=10
HEIGHT=10
ENTRY=0,0
EXIT=9,9
PERFECT=True
ALGORITHM=backtracker
OUTPUT_FILE=output.txt
SEED=42
# Optional color overrides:
# WALL_COLOR=pink
# PATH_COLOR=cyan
# PATTERN_COLOR=yellow
```

### Interactive menu
 
Once the program is running, the following options are available:
 
| Key | Action |
|---|---|
| `1` | Re-generate a new random maze |
| `2` | Show / hide the shortest path from entry to exit |
| `3` | Rotate wall color (cycles through a built-in palette) |
| `4` | Rotate path color |
| `5` | Rotate "42" pattern color |
| `6` | Quit |

## 🚀 Maze generation algorithm
 
Two algorithms are implemented:
 
- **Recursive Backtracker** (default): an iterative, stack-based depth-first carving of the grid. It always produces a perfect maze(a spanning tree: exactly one path between any two cells), which also tends to create long, winding corridors.
- **Binary Tree** (bonus): for each cell, a wall is opened towards north or east. It is simpler and faster, but on its own does not guarantee full connectivity once obstacles (the 42 pattern) are taken into account; our implementation tracks which cells are already connected and falls back to south/west when needed, so every non-42 cell always ends up reachable.
We chose the Recursive Backtracker as the default because it give the most natural-looking, unbiased maze (Binary Tree mazes have  visible diagonal bias towards one corner), and it directly satisfie the "exactly one path" requirement without any extra work.
 
Regardless of the algorithm chosen, two extra passes are always applied after generation:
 
- `PERFECT=False` adds a small number of random extra openings (loops) on top of the perfect maze, so more than one path can exist between cells.
- A corridor-width pass scans for any fully-open 3x3 (or larger) area - forbidden by the subject - and closes one wall to break it apart regardless of which algorithm or loop settings produced it.

## Code reusability
 
All maze generation and pathfinding logic lives in the `mazegen` package (`src/mazegen/`), which has no dependency on the terminal display code or the configuration file parser. It is built as a standalone, pip-installable package:
 
```bash
make build          # produces dist/mazegen-1.0.0-py3-none-any.whl and a copy on the root directory.
pip install mazegen-1.0.0-py3-none-any.whl
```
 
```python
from mazegen import MazeGenerator
 
generator = MazeGenerator(width=20, height=15, seed=42)
maze = generator.generate(algorithm="backtracker", perfect=True)
path = generator.solve(start=(0, 0), end=(19, 14))
```
 
See `src/mazegen/README.md` for the full package documentation, including how to pass custom parameters and access the generated structure and solution.
 
`a_maze_ing.py` only handles configuration parsing, the hexadecimal output file format, and the terminal display/menu - none of that is part of the reusable package.

## 📚 Resources

- [Recursive Backtracker and Binary Tree algorithms - Jamis Buck, "Maze Generation Algorithms"](https://weblog.jamisbuck.org/2011/2/7/maze-generation-algorithm-recap)
- [Python `typing` module documentation](https://docs.python.org/3/library/typing.html)
- [Python packaging user guide (src layout, build backend)](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [flake8](https://flake8.pycqa.org/) and [mypy](https://mypy.readthedocs.io/) documentation

**AI usage:** We wrote the initial implementation of every module ourselves, then used an AI assistant (Claude) as a code reviewer and
debugging aid on the already-written code.
 
## Team and project management
 
| Member | Role |
|---|---|
| jmesa-ci | Configuration parsing (`parser.py`) and the core maze data structure / terminal rendering (`write_maze.py`) / packaging. |
| lcristur | Generation algorithms, pathfinding, corridor/connectivity validation (`generator.py`), main program (`a_maze_ing.py`), packaging, and the fixes/review pass applied to the whole codebase. |
 
We split the project along the natural module boundaries early on: one of us owned config parsing and the maze/rendering data structures, the other owned the generation algorithms and the program entry point. This worked well because both halves only need to agree on the `Maze`/`Cell`/`Coord` interface, which we fixed early and rarely had to change.
 
What worked well: splitting by module meant we could work in parallel without touching the same files. What we would improve: we underestimated how many of the subject's correctness rules (connectivity, corridor width, PERFECT) only show up as bugs on specific maze sizes or seeds, so a chunk of the final days went into testing and fixing edge cases that a stricter test plan from the start would have caught sooner.
 
Tools used: `flake8` and `mypy --strict` throughout development to catch issues early, and an AI assistant for the final review pass described above.