```python
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
```

The next item is always the smallest of the streams' next items, so the heap holds one item from each stream, with the stream's place to break ties and the stream to read on from. `heapreplace` gives the smallest and puts its stream's next item in its place in one step, and a stream that runs out leaves the heap. Each item takes time in proportion to the logarithm of the streams, and the function reads nothing until it's asked for an item, as `heapq.merge` does too.

Collecting every item and sorting them is the slow way, and here it never finishes: the streams don't end. Looking through every stream's next item for each one given is slow in another way: {% $fig.looks %} looks for the tests' first {% $fig.items %} items.
