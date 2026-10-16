def decode(text):
    """text with each count[part] written out, inner ones first."""
    stack = []
    current, count = "", 0
    for character in text:
        if character.isdigit():
            count = count * 10 + int(character)
        elif character == "[":
            stack.append((current, count))
            current, count = "", 0
        elif character == "]":
            before, times = stack.pop()
            current = before + current * times
        else:
            current += character
    return current
