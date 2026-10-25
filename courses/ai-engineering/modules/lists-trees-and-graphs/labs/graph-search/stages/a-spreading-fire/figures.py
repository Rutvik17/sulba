# The largest test, as tests/test_fire.py sets it: a square forest whose trees run along every
# other row, joined at alternate ends, with the fire at one end.
SIDE = 401


def figures():
    trees = (SIDE + 1) // 2 * SIDE + SIDE // 2
    minutes = trees - 1
    return {
        "side": f"{SIDE}",
        "minutes": f"{minutes:,}",
        "squares": f"{SIDE * SIDE:,}",
        "looks": f"{minutes * SIDE * SIDE:,}",
    }
