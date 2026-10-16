```python
def sorted_pair(numbers, target):
    left, right = 0, len(numbers) - 1
    while left < right:
        total = numbers[left] + numbers[right]
        if total == target:
            return (left, right)
        if total < target:
            left += 1
        else:
            right -= 1
    return None
```

When the two numbers add up to too little, the left one can't be in any pair: the right one is the largest still in play, so every partner for the left one would add up to too little too. When they add up to too much, the right one can't be in a pair, for the same reason. Each step drops a number that has no partner, so no pair is missed, and the positions meet after at most `n` steps: time in proportion to the list, and no space besides the positions.

Looking up each number's partner with a binary search takes time in proportion to `$n \log n$`. The dict from Pair sums takes time in proportion to `n` but space too. Trying every pair means {% $fig.pairs %} pairs for the longest test's {% $fig.numbers %} numbers, far past the time limit.
