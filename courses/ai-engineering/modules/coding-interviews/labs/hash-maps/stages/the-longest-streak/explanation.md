```python
def longest_streak(numbers):
    present = set(numbers)
    best = 0
    for number in present:
        if number - 1 not in present:
            end = number
            while end + 1 in present:
                end += 1
            best = max(best, end - number + 1)
    return best
```

A streak starts at a number whose predecessor is missing, and only there does the loop count up. Every number is then stepped over once in the streak it belongs to, besides the one check of its predecessor, so the whole takes time in proportion to `n` on average, and the set takes as much space. Going through the set rather than the list also counts a repeated number once.

Counting up from every number, starts or not, walks each streak once for each of its numbers: for the longest test, one streak of {% $fig.numbers %} numbers, that's {% $fig.steps %} steps, far past the time limit.
