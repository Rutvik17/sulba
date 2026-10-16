from collections import Counter


def anagram_starts(text, word):
    """Where each run of text that's an anagram of word starts, in order."""
    needed = Counter(word)
    missing = len(word)
    starts = []
    for end, character in enumerate(text):
        if needed[character] > 0:
            missing -= 1
        needed[character] -= 1
        if end >= len(word):
            leaving = text[end - len(word)]
            needed[leaving] += 1
            if needed[leaving] > 0:
                missing += 1
        if missing == 0:
            starts.append(end - len(word) + 1)
    return starts
