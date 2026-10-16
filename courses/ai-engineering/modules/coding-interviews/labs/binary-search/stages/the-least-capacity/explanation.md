```python
def least_capacity(weights, days):
    def days_needed(capacity):
        needed, load = 1, 0
        for weight in weights:
            if load + weight > capacity:
                needed, load = needed + 1, 0
            load += weight
        return needed

    low, high = max(weights), sum(weights)
    while low < high:
        middle = (low + high) // 2
        if days_needed(middle) <= days:
            high = middle
        else:
            low = middle + 1
    return low
```

A ship must carry the heaviest package, and the total weight ships everything in one day, so the answer lies between them. A larger capacity never needs more days, so the capacities that ship in time are all those from the answer up, and a binary search over them finds it, counting each capacity's days in one pass. With `n` packages and a total weight `W`, that's time in proportion to `$n \log W$`.

Trying each capacity from the heaviest package up instead counts the days for {% $fig.tried %} capacities in the longest test, each in a pass over {% $fig.packages %} packages, far past the time limit.
