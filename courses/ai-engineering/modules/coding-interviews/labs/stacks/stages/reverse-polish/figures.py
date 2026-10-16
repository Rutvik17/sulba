# The longest test, as tests/test_rpn.py sets it: NUMBERS numbers, then the operators that add
# them up, and the tokens that finding the first operator from the start reads, once for each
# operator, with one number fewer before it each time.
NUMBERS = 50_001


def figures():
    operators = NUMBERS - 1
    reads = sum(NUMBERS - done + 1 for done in range(operators))
    return {
        "tokens": f"{NUMBERS + operators:,}",
        "numbers": f"{NUMBERS:,}",
        "operators": f"{operators:,}",
        "reads": f"{reads:,}",
    }
