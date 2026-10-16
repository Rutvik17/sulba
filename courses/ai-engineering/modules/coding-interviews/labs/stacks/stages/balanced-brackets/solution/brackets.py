def balanced(text):
    """Whether every bracket in text is closed by its own kind, in the right order."""
    pairs = {")": "(", "]": "[", "}": "{"}
    opened = []
    for character in text:
        if character in "([{":
            opened.append(character)
        elif character in pairs:
            if not opened or opened.pop() != pairs[character]:
                return False
    return not opened
