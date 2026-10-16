```python
def first_and_last(numbers, value):
    def boundary(past):
        low, high = 0, len(numbers)
        while low < high:
            middle = (low + high) // 2
            if numbers[middle] < value or (past and numbers[middle] == value):
                low = middle + 1
            else:
                high = middle
        return low

    first = boundary(past=False)
    if first == len(numbers) or numbers[first] != value:
        return None
    return (first, boundary(past=True) - 1)
```

`boundary(False)` finds the first number not smaller than `value`, and `boundary(True)` the first number larger, by also moving past numbers equal to it. If the first is past the end or isn't `value`, the value isn't there; otherwise its last position is one before the first larger number. Two searches take time in proportion to `$\log n$`, however long the run of equal numbers.

Finding the first position and then walking to the end of the run reads up to {% $fig.run %} positions for each of the longest test's {% $fig.searches %} searches, {% $fig.reads %} in all, far past the time limit.
