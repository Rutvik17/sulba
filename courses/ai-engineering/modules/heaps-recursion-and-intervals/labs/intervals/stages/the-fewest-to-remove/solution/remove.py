def fewest_removed(meetings):
    kept, last_end = 0, None
    for start, end in sorted(meetings, key=lambda meeting: meeting[1]):
        if last_end is None or start >= last_end:
            kept += 1
            last_end = end
    return len(meetings) - kept
