```python
from collections import Counter


def anagram_starts(text, word):
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
```

`needed` holds how many more of each character the window needs, below zero for characters it holds too many of, and `missing` adds up the characters still needed. A character coming in fills a need if there was one, and a character leaving reopens one if the window then lacks it. Once the window has the word's length, nothing missing means it holds exactly the word's characters, since it has room for no others. Each character comes in once and leaves once: time in proportion to the text, and space for the different characters.

Sorting each run and comparing it with the sorted word sorts {% $fig.runs %} runs of {% $fig.length %} characters for the longest test, far past the time limit.
