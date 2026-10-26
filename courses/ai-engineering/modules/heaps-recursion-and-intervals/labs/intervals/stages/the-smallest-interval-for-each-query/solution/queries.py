import heapq


def smallest_containing(intervals, queries):
    intervals = sorted(intervals)
    found = {}
    reach = []
    place = 0
    for query in sorted(set(queries)):
        while place < len(intervals) and intervals[place][0] <= query:
            left, right = intervals[place]
            heapq.heappush(reach, (right - left + 1, right))
            place += 1
        while reach and reach[0][1] < query:
            heapq.heappop(reach)
        found[query] = reach[0][0] if reach else -1
    return [found[query] for query in queries]
