```python
from collections import Counter


def count_runs(numbers, target):
    sums = Counter({0: 1})
    total = count = 0
    for number in numbers:
        total += number
        count += sums[total - target]
        sums[total] += 1
    return count
```

`total` is the sum of the numbers so far, a prefix sum. A run that ends at the current number adds up to `target` exactly when the prefix sum before its first number was `total - target`, so the number of runs ending here is the number of earlier prefix sums with that value, which the `Counter` holds. It starts with `{0: 1}` for the empty prefix, so that runs starting at the first number count too. One pass, with time in proportion to the list and as much space for the counts.

A window that grows and shrinks works only when every number is positive: with negative numbers, adding a number can lower the sum, so the window can't tell which way to move. Trying every run instead means {% $fig.runs %} runs for the longest test's {% $fig.numbers %} numbers, far past the time limit.
