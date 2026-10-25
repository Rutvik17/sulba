from collections import defaultdict, deque


def ladder(start, end, words):
    """The words in the shortest chain from start to end, each a letter away from the one
    before it, every word after start from words, or 0 if there's no chain."""
    words = set(words)
    if end not in words:
        return 0
    # Each word under every pattern it fits with one letter left blank: "cold" under "*old",
    # "c*ld", "co*d" and "col*".
    patterns = defaultdict(list)
    for word in words | {start}:
        for place in range(len(word)):
            patterns[word[:place] + "*" + word[place + 1 :]].append(word)
    chain = {start: 1}
    waiting = deque([start])
    while waiting:
        word = waiting.popleft()
        if word == end:
            return chain[word]
        for place in range(len(word)):
            for near in patterns.pop(word[:place] + "*" + word[place + 1 :], []):
                if near not in chain:
                    chain[near] = chain[word] + 1
                    waiting.append(near)
    return 0
