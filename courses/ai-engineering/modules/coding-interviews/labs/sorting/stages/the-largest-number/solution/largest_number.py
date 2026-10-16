from functools import cmp_to_key


def largest_number(numbers):
    """The largest number that writing all of numbers side by side can make, as a string."""

    def order(a, b):
        if a + b > b + a:
            return -1
        return 1 if a + b < b + a else 0

    digits = sorted(map(str, numbers), key=cmp_to_key(order))
    return "".join(digits).lstrip("0") or "0"
