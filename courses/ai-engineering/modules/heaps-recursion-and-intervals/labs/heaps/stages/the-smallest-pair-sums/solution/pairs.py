import heapq


def smallest_pairs(first, second, k):
    if not first or not second:
        return []
    frontier = [(first[i] + second[0], i, 0) for i in range(min(k, len(first)))]
    heapq.heapify(frontier)
    pairs = []
    while frontier and len(pairs) < k:
        _, i, j = heapq.heappop(frontier)
        pairs.append((first[i], second[j]))
        if j + 1 < len(second):
            heapq.heappush(frontier, (first[i] + second[j + 1], i, j + 1))
    return pairs
