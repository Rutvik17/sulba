import sys

# The longest test, as tests/test_add.py sets it.
DIGITS = 200_000


def figures():
    return {
        "digits": f"{DIGITS:,}",
        "limit": f"{sys.int_info.default_max_str_digits:,}",
    }
