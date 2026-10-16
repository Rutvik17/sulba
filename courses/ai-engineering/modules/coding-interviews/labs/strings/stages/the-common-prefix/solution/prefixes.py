def common_prefix(words):
    """The longest start that every word shares, or "" if they share none."""
    if not words:
        return ""
    shortest = min(words, key=len)
    for position, character in enumerate(shortest):
        if any(word[position] != character for word in words):
            return shortest[:position]
    return shortest
