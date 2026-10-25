# The tests' largest grid and longest word, as tests/test_grid.py sets them.
SIDE = 40
PREFIX = 30


def figures():
    # A path's first step has 4 ways to go, and each after it at most 3.
    return {
        "side": f"{SIDE}",
        "cells": f"{SIDE * SIDE:,}",
        "prefix": f"{PREFIX}",
        "paths": f"{4 * 3 ** (PREFIX - 2):,}",
    }
