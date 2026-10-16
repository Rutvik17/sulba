import heapq


def kth_largest(numbers, k):
    """The kth largest of numbers, counting repeats."""
    heap = []
    for number in numbers:
        if len(heap) < k:
            heapq.heappush(heap, number)
        elif number > heap[0]:
            heapq.heapreplace(heap, number)
    return heap[0]
