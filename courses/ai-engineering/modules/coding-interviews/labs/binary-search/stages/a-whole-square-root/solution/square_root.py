def square_root(n):
    """The largest whole number whose square is at most n."""
    low, high = 0, n
    while low < high:
        middle = (low + high + 1) // 2
        if middle * middle <= n:
            low = middle
        else:
            high = middle - 1
    return low
