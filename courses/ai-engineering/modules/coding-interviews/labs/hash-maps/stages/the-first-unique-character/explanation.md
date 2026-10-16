```python
from collections import Counter


def first_unique(text):
    counts = Counter(text)
    for position, character in enumerate(text):
        if counts[character] == 1:
            return position
    return None
```

The first pass counts every character, and the second stops at the first one that appeared once. Each pass takes time in proportion to the text, and the counts take space in proportion to the number of different characters. An empty text, or one where every character repeats, gets through the second pass without returning, so it gives `None`.

`text.count(character)` for each position instead reads the whole text again for every character: up to {% $fig.reads %} characters read for the longest test's {% $fig.characters %}, far past the time limit.
