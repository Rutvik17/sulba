import heapq


def delay(computers, links, start):
    """The minutes until a message sent from start has reached every computer, or -1 if some
    computer can't be reached."""
    onward = [[] for _ in range(computers + 1)]
    for source, target, minutes in links:
        onward[source].append((target, minutes))
    arrived = {}
    waiting = [(0, start)]
    while waiting:
        time, computer = heapq.heappop(waiting)
        if computer in arrived:
            continue
        arrived[computer] = time
        for target, minutes in onward[computer]:
            if target not in arrived:
                heapq.heappush(waiting, (time + minutes, target))
    return max(arrived.values()) if len(arrived) == computers else -1
