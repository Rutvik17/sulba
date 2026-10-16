# The longest test, as tests/test_products.py sets it: its numbers, and the multiplications that
# multiplying the other numbers into a product of 1 takes for every position.
NUMBERS = 100_000


def figures():
    return {
        "numbers": f"{NUMBERS:,}",
        "multiplications": f"{NUMBERS * (NUMBERS - 1):,}",
    }
