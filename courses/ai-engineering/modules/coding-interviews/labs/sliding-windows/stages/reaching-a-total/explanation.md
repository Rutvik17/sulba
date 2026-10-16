```python
def shortest_reach(numbers, target):
    best = 0
    total = start = 0
    for end, number in enumerate(numbers):
        total += number
        while total >= target:
            if best == 0 or end - start + 1 < best:
                best = end - start + 1
            total -= numbers[start]
            start += 1
    return best
```

For each end, the window shrinks from its start for as long as its sum still reaches the target, so it finds the shortest run reaching it that ends there. A start that was dropped never needs to come back: with every number positive, the same start with a later end would only make a longer run. Each number joins the window once and leaves it at most once, so the whole takes time in proportion to the list, with no extra space.

The window works only because every number is positive. Trying every run instead means {% $fig.runs %} runs for the longest test's {% $fig.numbers %} numbers, far past the time limit.
