import pytest

from sudoku import solved

PUZZLES = [
    ".2..8.5..9.........3.94....67...1.2..1....3.8..4..9.6....2.38.6......2....7.6....",
    ".6.....389...85...54..........4.3.7.1.......9...6.21...7.9.1.6.4.12...........7..",
    ".3....5.....9567....6.7..1.8..31...6.5.4....9.....2...3.....1..1.9....2..8......7",
    "47........2.3.1..5.1.54...675...9....4.823.......1...29....8..3......7.........2.",
    ".5..317.2.6.7...8....46.....849...5.........3..2..7.........5..1...9..3.....149.8",
    "...2..74.45.6...9..1.......39...5..71.53..........4......47.5.6..7593............",
    "2.....19.3...9..2....2.53.7.......3...8..6........18...65.1..8...7..3..6..96....5",
    ".92.1....5.17..2..........33..15.7.9...6.3..5....2.........9...71..34...26....4..",
]
HARDEST = [
    "6...9.5.4...63.....5.4......25...........3..8.7..51..6.4..2.7.......71...6....8.2",
    "..7.....3..8..5....1.3...4...4..7.......4..1.....9356...2...3917....2........825.",
    "7.549..3.....2.......1..8...4.9....5....7.4........68..7.8..14.2.....7.6...74....",
    "....8..4....2..9..16.7......8..9.5...2............6..99.7.1...2.52....84..6.4....",
    "...21..9..1...37.2.238.5.............5.....7...1...25...91..4....23.85.1....26...",
]


def rows(puzzle):
    return [puzzle[start : start + 9] for start in range(0, 81, 9)]


def fits(puzzle, grid):
    """Whether the grid is a filled sudoku that keeps the puzzle's clues."""
    if len(grid) != 9 or any(len(row) != 9 for row in grid):
        return False
    if any(
        clue not in (".", grid[place // 9][place % 9])
        for place, clue in enumerate(puzzle)
    ):
        return False
    columns = ["".join(row[column] for row in grid) for column in range(9)]
    boxes = [
        "".join(grid[r][c] for r in range(top, top + 3) for c in range(left, left + 3))
        for top in (0, 3, 6)
        for left in (0, 3, 6)
    ]
    return all(sorted(group) == list("123456789") for group in grid + columns + boxes)


@pytest.mark.id("tst_cxu834")
def test_solved():
    """Fills the puzzle so every row, column and box holds 1 to 9"""
    puzzle = "..4....5...3....48....63........2..4..5....9.19...7.6...7.3...59....6...5..7..2.."
    assert fits(puzzle, solved(rows(puzzle)))


@pytest.mark.id("tst_wlfql1")
def test_edges():
    """Returns a filled grid as it is, and fills a grid with one empty cell"""
    puzzle = PUZZLES[0]
    filled = solved(rows(puzzle))
    assert solved(filled) == filled
    one_empty = list("".join(filled))
    one_empty[40] = "."
    assert solved(rows("".join(one_empty))) == filled


@pytest.mark.id("tst_w24gk0")
def test_puzzles():
    """Solves a set of puzzles"""
    for puzzle in PUZZLES:
        assert fits(puzzle, solved(rows(puzzle)))


@pytest.mark.id("tst_es8hnz")
def test_long():
    """Solves the hardest puzzles in time"""
    for puzzle in HARDEST:
        assert fits(puzzle, solved(rows(puzzle)))
