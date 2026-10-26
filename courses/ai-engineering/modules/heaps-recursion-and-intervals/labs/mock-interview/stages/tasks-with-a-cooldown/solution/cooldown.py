from collections import Counter


def least_time(tasks, cooldown):
    counts = Counter(tasks).values()
    most = max(counts, default=0)
    tied = sum(1 for count in counts if count == most)
    return max(len(tasks), (most - 1) * (cooldown + 1) + tied)
