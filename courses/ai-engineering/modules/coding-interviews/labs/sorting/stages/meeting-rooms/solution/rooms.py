def rooms_needed(meetings):
    """The fewest rooms that hold every meeting."""
    starts = sorted(start for start, _ in meetings)
    ends = sorted(end for _, end in meetings)
    rooms = most = ended = 0
    for start in starts:
        while ends[ended] <= start:
            ended += 1
            rooms -= 1
        rooms += 1
        most = max(most, rooms)
    return most
