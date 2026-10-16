def best_profit(prices):
    """The most made by buying on one day and selling on a later day, or 0."""
    best = 0
    lowest = float("inf")
    for price in prices:
        lowest = min(lowest, price)
        best = max(best, price - lowest)
    return best
