import heapq


def medians(numbers):
    low, high = [], []
    found = []
    for number in numbers:
        if low and number > low[0]:
            heapq.heappush(high, number)
        else:
            heapq.heappush_max(low, number)
        if len(low) > len(high) + 1:
            heapq.heappush(high, heapq.heappop_max(low))
        elif len(high) > len(low):
            heapq.heappush_max(low, heapq.heappop(high))
        if len(low) > len(high):
            found.append(float(low[0]))
        else:
            found.append((low[0] + high[0]) / 2)
    return found
