```python
def rotated_search(numbers, value):
    low, high = 0, len(numbers) - 1
    while low <= high:
        middle = (low + high) // 2
        if numbers[middle] == value:
            return middle
        if numbers[low] <= numbers[middle]:
            if numbers[low] <= value < numbers[middle]:
                high = middle - 1
            else:
                low = middle + 1
        elif numbers[middle] < value <= numbers[high]:
            low = middle + 1
        else:
            high = middle - 1
    return None
```

The rotation point falls in at most one of the halves either side of the middle, so the other half is in order, and `numbers[low] <= numbers[middle]` says whether it's the left one. A half in order holds `value` only if it lies between its ends, so the search goes into that half or the other, halving what's left at each step: time in proportion to `$\log n$`, with no extra space.

`numbers.index(value)` reads the list from its start, up to {% $fig.numbers %} reads for each of the longest test's {% $fig.searches %} searches, {% $fig.reads %} in all, far past the time limit.
