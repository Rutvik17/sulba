```python
import heapq
from collections import Counter


def reorganized(text):
    counts = [(count, letter) for letter, count in Counter(text).items()]
    heapq.heapify_max(counts)
    letters, held = [], None
    while counts:
        count, letter = heapq.heappop_max(counts)
        letters.append(letter)
        if held:
            heapq.heappush_max(counts, held)
        held = (count - 1, letter) if count > 1 else None
    return "".join(letters) if held is None else ""
```

Placing the letter with the most left, never the one just placed, keeps the counts as even as they can be: a letter can't run out of others to stand between its copies unless it has more than half the letters, rounded up, and then no order works. The heap holds each letter with its count, the letter just placed waits out one turn before it goes back, and a letter still waiting at the end means the text can't be ordered. Each letter placed takes time in proportion to the logarithm of the letters that differ.

Trying the orders of the letters until one keeps alike letters apart is the slow way: the longest test's letters have a number of orders with {% $fig.digits %} digits.
