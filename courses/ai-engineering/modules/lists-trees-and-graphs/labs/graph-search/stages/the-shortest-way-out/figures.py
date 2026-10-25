# The largest tests, as tests/test_maze.py sets them: a square maze of corridors along every other
# row, joined at alternate ends, from the start in one corner to the exit at the far end, and an
# open square room. And the ways from one corner of an open 5 by 5 square to the opposite one
# that never revisit a square.
SIDE = 401
ROOM = 300
OPEN = 5


def ways(side):
    """The ways from one corner of an open square to the opposite one, never revisiting a
    square."""
    seen, count, waiting = {(0, 0)}, 0, [((0, 0), 0)]
    # Each entry is a square on the current way and the next of its four moves to try.
    while waiting:
        (y, x), move = waiting.pop()
        if (y, x) == (side - 1, side - 1):
            count += 1
            seen.discard((y, x))
            continue
        if move == 4:
            seen.discard((y, x))
            continue
        waiting.append(((y, x), move + 1))
        dy, dx = ((-1, 0), (1, 0), (0, -1), (0, 1))[move]
        near = (y + dy, x + dx)
        if 0 <= near[0] < side and 0 <= near[1] < side and near not in seen:
            seen.add(near)
            waiting.append((near, 0))
    return count


def figures():
    corridors = (SIDE + 1) // 2
    return {
        "side": f"{SIDE}",
        "room": f"{ROOM}",
        "steps": f"{corridors * SIDE + SIDE // 2 - 1:,}",
        "paths": f"{ways(OPEN):,}",
    }
