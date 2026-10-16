def longest_unique(text):
    """The length of the longest run of adjacent characters with no character twice."""
    last = {}
    start = best = 0
    for position, character in enumerate(text):
        if last.get(character, -1) >= start:
            start = last[character] + 1
        last[character] = position
        best = max(best, position - start + 1)
    return best
