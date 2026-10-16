def most_frequent(items, k):
    """The k items that appear most often, most frequent first, ties by first appearance."""
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return sorted(counts, key=lambda item: -counts[item])[:k]
