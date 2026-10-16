```python
from collections import Counter


def smallest_cover(text, letters):
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
```

`needed` holds how many more of each character the window needs, below zero for characters it has to spare, and `missing` adds up the ones still needed. Once nothing is missing, the start moves past characters the window can spare, which leaves the shortest covering run that ends here. The window then gives up its first character, which it needed, and grows again. Each character joins the window once and leaves it at most once, and only a shorter run replaces `best`, so of runs that tie, the first stays. The whole takes time in proportion to the text, and space in proportion to the different characters.

Growing a run from every start until it covers the letters reads up to {% $fig.reads %} characters for the longest test, far past the time limit.
