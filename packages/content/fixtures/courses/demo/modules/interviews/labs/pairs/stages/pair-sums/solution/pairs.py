def pair_sum(numbers, target):
    """The positions of the two numbers that add up to target, or None."""
    seen = {}
    for position, number in enumerate(numbers):
        partner = seen.get(target - number)
        if partner is not None:
            return (partner, position)
        seen.setdefault(number, position)
    return None
