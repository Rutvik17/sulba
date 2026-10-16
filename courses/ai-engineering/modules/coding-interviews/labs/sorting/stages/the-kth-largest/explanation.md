```python
import heapq


def kth_largest(numbers, k):
    heap = []
    for number in numbers:
        if len(heap) < k:
            heapq.heappush(heap, number)
        elif number > heap[0]:
            heapq.heapreplace(heap, number)
    return heap[0]
```

The heap holds the `k` largest numbers so far, smallest at `heap[0]`. A new number belongs among them only when it's larger than that smallest one, which it replaces, so at the end `heap[0]` is the `k`th largest, repeats counted. Each push or replace takes time in proportion to `$\log k$`: the whole takes `$n \log k$`, and `k` places of space. `heapq.nlargest(k, numbers)[-1]` does the same. `sorted(numbers)[-k]` takes `$n \log n$`, which also fits the time limit.

Taking out the largest `k` times, with `max` and `remove`, reads the list {% $fig.k %} times for the longest test's {% $fig.numbers %} numbers, far past the time limit.
