from collections import Counter


def longest_with_kinds(items, k):
    """The length of the longest run of adjacent items holding at most k values."""
    counts = Counter()
    start = best = 0
    for end, item in enumerate(items):
        counts[item] += 1
        while len(counts) > k:
            counts[items[start]] -= 1
            if counts[items[start]] == 0:
                del counts[items[start]]
            start += 1
        best = max(best, end - start + 1)
    return best
