import heapq


def free_time(schedules):
    busy = heapq.merge(*schedules)
    found = []
    first = next(busy, None)
    if first is None:
        return found
    end = first[1]
    for start, finish in busy:
        if start > end:
            found.append((end, start))
        end = max(end, finish)
    return found
