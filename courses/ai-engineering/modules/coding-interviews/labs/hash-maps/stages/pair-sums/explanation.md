```python
def pair_sum(numbers, target):
    seen = {}
    for j, number in enumerate(numbers):
        i = seen.get(target - number)
        if i is not None:
            return (i, j)
        seen.setdefault(number, j)
    return None
```

The loop goes through the positions that could end a pair in order, and for each looks up the partner it needs among the numbers before it. The first `j` that finds a partner ends the earliest pair, and `setdefault` keeps the first position of each number, so `i` is the earliest start for that `j`. Looking the partner up before adding the number keeps a number from pairing with itself, while a second equal number finds the first.

A dict lookup takes constant time on average, so the pass takes time in proportion to the list, and the dict takes as much space. Trying every pair instead means {% $fig.pairs %} pairs for the longest test's {% $fig.numbers %} numbers, far past the time limit.
