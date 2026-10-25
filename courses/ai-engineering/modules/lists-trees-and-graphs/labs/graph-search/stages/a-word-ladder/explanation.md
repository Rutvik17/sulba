```python
from collections import defaultdict, deque


def ladder(start, end, words):
    words = set(words)
    if end not in words:
        return 0
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
```

The words are a graph whose links are never written down: two words are linked when they're a letter apart. A breadth-first search from `start` reaches each word first by a shortest ladder, so `end`'s count when it's taken is the answer.

The patterns find a word's links without looking at every other word. Filing `n` words of `L` letters takes `n × L` patterns, and a pattern's words are followed once, since every word under it is then in `chain`, so the search does work in proportion to the patterns and their words. Comparing every pair of words to find the links is the slow way: for the longest test's {% $fig.words %} words, that's {% $fig.pairs %} pairs, each compared letter by letter.
