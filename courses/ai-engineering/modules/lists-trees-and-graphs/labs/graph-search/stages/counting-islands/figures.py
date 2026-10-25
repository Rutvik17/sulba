import sys

# The largest test, as tests/test_islands.py sets it: a square map whose island runs along every
# other row and joins them at alternate ends.
SIDE = 401


def figures():
    full = (SIDE + 1) // 2
    joins = SIDE // 2
    # The explanation says a recursive flood of the island goes past the recursion limit.
    assert sys.getrecursionlimit() < full * SIDE + joins
    return {"side": f"{SIDE}", "cells": f"{full * SIDE + joins:,}"}
