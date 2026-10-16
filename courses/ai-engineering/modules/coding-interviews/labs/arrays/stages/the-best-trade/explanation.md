```python
def best_profit(prices):
    best = 0
    lowest = float("inf")
    for price in prices:
        lowest = min(lowest, price)
        best = max(best, price - lowest)
    return best
```

The best trade that sells on a given day buys at the lowest price before it, so one pass that keeps the lowest price so far finds the best trade for every selling day. It takes time in proportion to the number of days, and no extra space. Updating `lowest` before `best` lets a day pair with itself, a trade that makes `0`, which is also the answer when prices only fall.

Trying every pair of days instead means {% $fig.pairs %} pairs for the longest test's {% $fig.prices %} prices, far past the time limit.
