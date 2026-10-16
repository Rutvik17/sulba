from collections import Counter


def smallest_cover(text, letters):
    """The shortest run of adjacent characters in text that covers letters, or ""."""
    needed = Counter(letters)
    missing = len(letters)
    best = ""
    start = 0
    for end, character in enumerate(text):
        if needed[character] > 0:
            missing -= 1
        needed[character] -= 1
        if missing == 0:
            while needed[text[start]] < 0:
                needed[text[start]] += 1
                start += 1
            if not best or end - start + 1 < len(best):
                best = text[start : end + 1]
            needed[text[start]] += 1
            missing += 1
            start += 1
    return best
