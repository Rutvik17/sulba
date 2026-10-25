import heapq


def merged(streams):
    heads = []
    for place, stream in enumerate(streams):
        stream = iter(stream)
        for first in stream:
            heads.append((first, place, stream))
            break
    heapq.heapify(heads)
    while heads:
        value, place, stream = heads[0]
        yield value
        for following in stream:
            heapq.heapreplace(heads, (following, place, stream))
            break
        else:
            heapq.heappop(heads)
