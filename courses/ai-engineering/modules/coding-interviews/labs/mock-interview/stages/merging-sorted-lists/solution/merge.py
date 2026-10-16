import heapq


def merge_sorted(lists):
    """Every number in the sorted lists, in one sorted list."""
    heap = [(numbers[0], which, 0) for which, numbers in enumerate(lists) if numbers]
    heapq.heapify(heap)
    merged = []
    while heap:
        number, which, at = heapq.heappop(heap)
        merged.append(number)
        if at + 1 < len(lists[which]):
            heapq.heappush(heap, (lists[which][at + 1], which, at + 1))
    return merged
