```python
def square_root(n):
    low, high = 0, n
    while low < high:
        middle = (low + high + 1) // 2
        if middle * middle <= n:
            low = middle
        else:
            high = middle - 1
    return low
```

`low` always has a square at most `n`, and every number above `high` has a square above it, so when they meet, `low` is the answer. The middle is rounded up because `low` can take the middle's value: rounded down, `low` and `high` one apart would never meet. Each step halves the range, so a number of `d` digits takes about `$3.3 d$` steps, and whole numbers keep every square exact.

`int(math.sqrt(n))` goes through a float, which holds about 16 significant digits, so for the tests' largest number it gives a root that's wrong in its later digits. Counting up from `0` until the square passes `n` takes {% $fig.steps %} steps for that number, far past the time limit.
