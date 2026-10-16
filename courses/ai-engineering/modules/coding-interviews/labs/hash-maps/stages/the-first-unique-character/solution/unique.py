from collections import Counter


def first_unique(text):
    """The position of the first character that appears only once in text, or None."""
    counts = Counter(text)
    for position, character in enumerate(text):
        if counts[character] == 1:
            return position
    return None
