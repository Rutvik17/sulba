```python
def zero_triples(numbers):
    numbers = sorted(numbers)
    found = []
    for i, first in enumerate(numbers):
        if i > 0 and first == numbers[i - 1]:
            continue
        left, right = i + 1, len(numbers) - 1
        while left < right:
            total = first + numbers[left] + numbers[right]
            if total < 0:
                left += 1
            elif total > 0:
                right -= 1
            else:
                found.append((first, numbers[left], numbers[right]))
                left += 1
                while left < right and numbers[left] == numbers[left - 1]:
                    left += 1
                right -= 1
    return found
```

After sorting, each first number takes the numbers after it as its pair, and two positions moving inwards find every pair that adds up to `-first` in one pass. Skipping a first number equal to the one before, and moving `left` past numbers equal to the one just used, gives each triple once, and since the triples come out with `first`, then `numbers[left]`, rising, they come out sorted. Sorting takes time in proportion to `$n \log n$` and the passes `$n^2$`, and the space goes to the sorted copy and the triples found.

Trying every three positions instead means {% $fig.triples %} triples for the longest test's {% $fig.numbers %} numbers, far past the time limit.
