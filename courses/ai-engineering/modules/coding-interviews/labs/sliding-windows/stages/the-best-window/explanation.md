```python
def best_window(numbers, k):
    total = best = sum(numbers[:k])
    for i in range(k, len(numbers)):
        total += numbers[i] - numbers[i - k]
        best = max(best, total)
    return best
```

The first window's sum takes `k` additions, and each step after it adds the number that comes in and takes away the one that drops out, so every window's sum costs one step. The whole takes time in proportion to the list, with no extra space.

Summing each window afresh takes `k` additions for each of the windows: {% $fig.additions %} additions for the longest test's {% $fig.numbers %} numbers, far past the time limit.
