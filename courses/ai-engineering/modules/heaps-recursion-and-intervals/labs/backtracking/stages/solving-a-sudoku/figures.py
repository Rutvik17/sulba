# The tests' puzzles, as tests/test_sudoku.py gives them.
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


def tries(puzzle, fewest_first):
    """How many digits a search places before the puzzle is filled."""
    cells = list(puzzle)
    groups = [set() for _ in range(27)]
    of = [
        (place // 9, 9 + place % 9, 18 + place // 27 * 3 + place % 9 // 3)
        for place in range(81)
    ]
    for place, digit in enumerate(cells):
        if digit != ".":
            for group in of[place]:
                groups[group].add(digit)
    empty = [place for place in range(81) if cells[place] == "."]
    placed = 0

    def options(place):
        row, column, box = (groups[group] for group in of[place])
        return [
            digit
            for digit in "123456789"
            if digit not in row and digit not in column and digit not in box
        ]

    def fill(left):
        nonlocal placed
        if not left:
            return True
        place = (
            min(left, key=lambda each: len(options(each))) if fewest_first else left[0]
        )
        rest = [each for each in left if each != place]
        for digit in options(place):
            cells[place] = digit
            placed += 1
            for group in of[place]:
                groups[group].add(digit)
            if fill(rest):
                return True
            for group in of[place]:
                groups[group].remove(digit)
        cells[place] = "."
        return False

    fill(empty)
    return placed


def figures():
    hardest = HARDEST[-1]
    return {
        "fewest": f"{min(81 - puzzle.count('.') for puzzle in HARDEST)}",
        "plain": f"{tries(hardest, False):,}",
        "fewest_first": f"{tries(hardest, True):,}",
    }
