```python
import heapq


def delay(computers, links, start):
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
```

This is Dijkstra's algorithm. The earliest arrival in the heap is final: any other way to that computer leaves through a computer reached no sooner, and links never take less than 0 minutes, so it can only arrive later. A computer can be in the heap several times, by different ways; the first of them taken is its time, and the rest are passed over. `heapq`'s documentation describes its heaps as "binary trees for which every parent node has a value less than or equal to any of its children", so taking the smallest and adding an arrival each take time in proportion to the heap's height, and the search takes time in proportion to `$(n + m) \log m$` for `n` computers and `m` links.

Finding the soonest computer by looking through every one not yet reached is the slow way: for the largest test that's a pass over the {% $fig.computers %} computers for each of them, {% $fig.looks %} looks. A breadth-first search alone counts links, not minutes, and finds the wrong times when links take different minutes.
