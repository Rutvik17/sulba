# The tests' largest number, as tests/test_square_root.py sets it: how many digits it has, and
# the steps that counting up from 0 until a square passes it takes.
ROOT = 10**30 + 7
LARGEST = ROOT * ROOT - 1


def figures():
    return {"digits": f"{len(str(LARGEST))}", "steps": f"{ROOT:,}"}
