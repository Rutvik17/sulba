def count(choices, choice):
    """How many of choices equal choice."""
    return sum(1 for each in choices if each == choice)


def share(choices, choice):
    """The fraction of choices that equal choice."""
    return count(choices, choice) / len(choices)
