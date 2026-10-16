def best_window(numbers, k):
    """The largest sum of k adjacent numbers."""
    total = best = sum(numbers[:k])
    for i in range(k, len(numbers)):
        total += numbers[i] - numbers[i - k]
        best = max(best, total)
    return best
