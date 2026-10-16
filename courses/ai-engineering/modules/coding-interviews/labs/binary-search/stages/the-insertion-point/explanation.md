```python
def insertion_point(numbers, value):
    low, high = 0, len(numbers)
    while low < high:
        middle = (low + high) // 2
        if numbers[middle] < value:
            low = middle + 1
        else:
            high = middle
    return low
```

Every number before `low` is smaller than `value`, and every number from `high` on is not, from the start, when both sets are empty, to the end, when the bounds meet at the answer. Each step looks at the middle and moves one bound past it or onto it, halving what's left, so a search takes time in proportion to `$\log n$`, with no extra space. `high` starts at `len(numbers)`, so a value larger than every number goes at the end.

Reading the list from the start until the first number not smaller than `value` takes up to {% $fig.numbers %} reads for each of the longest test's {% $fig.searches %} searches, {% $fig.reads %} in all, far past the time limit.
