def inserted(intervals, new):
    start, end = new
    found = []
    place = 0
    while place < len(intervals) and intervals[place][1] < start:
        found.append(intervals[place])
        place += 1
    while place < len(intervals) and intervals[place][0] <= end:
        start = min(start, intervals[place][0])
        end = max(end, intervals[place][1])
        place += 1
    found.append((start, end))
    found.extend(intervals[place:])
    return found
