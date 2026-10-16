```python
from itertools import groupby


def encode(text):
    return "".join(f"{character}{len(list(run))}" for character, run in groupby(text))


def decode(encoded):
    pieces = []
    position = 0
    while position < len(encoded):
        character = encoded[position]
        start = position = position + 1
        while position < len(encoded) and encoded[position].isdigit():
            position += 1
        pieces.append(character * int(encoded[start:position]))
    return "".join(pieces)
```

`groupby` gives each run in turn, so `encode` writes each character with its run's length. `decode` reads a character, then the digits after it, however many there are, and repeats the character that many times. Because the texts hold no digits, each digit belongs to a length and each other character starts a run. Both take time in proportion to the text.

Both build their answer with `"".join`, in time in proportion to its length. Adding to a string with `+=` in a loop is as fast only when CPython can grow the string in place, which it doesn't promise: otherwise each `+=` copies the whole string, and the work grows with the square of the text's length.
