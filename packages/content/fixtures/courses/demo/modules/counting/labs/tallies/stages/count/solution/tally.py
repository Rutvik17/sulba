def count(choices, choice):
    """How many of choices equal choice."""
    return sum(1 for each in choices if each == choice)
