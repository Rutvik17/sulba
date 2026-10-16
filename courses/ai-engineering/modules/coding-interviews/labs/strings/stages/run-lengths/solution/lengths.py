from itertools import groupby


def encode(text):
    """Each run of one character as the character followed by its length."""
    return "".join(f"{character}{len(list(run))}" for character, run in groupby(text))


def decode(encoded):
    """The text that encode gave encoded."""
    pieces = []
    position = 0
    while position < len(encoded):
        character = encoded[position]
        start = position = position + 1
        while position < len(encoded) and encoded[position].isdigit():
            position += 1
        pieces.append(character * int(encoded[start:position]))
    return "".join(pieces)
