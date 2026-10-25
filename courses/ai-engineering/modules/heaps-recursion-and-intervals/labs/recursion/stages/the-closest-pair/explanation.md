```python
import heapq


def squared(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def closest(points):
    by_x = sorted(points)

    def search(lo, hi):
        if hi - lo <= 3:
            here = sorted(by_x[lo:hi], key=lambda point: point[1])
            best = min(squared(a, b) for i, a in enumerate(here) for b in here[i + 1 :])
            return best, here
        mid = (lo + hi) // 2
        line = by_x[mid][0]
        left, left_by_y = search(lo, mid)
        right, right_by_y = search(mid, hi)
        best = min(left, right)
        by_y = list(heapq.merge(left_by_y, right_by_y, key=lambda point: point[1]))
        strip = [point for point in by_y if (point[0] - line) ** 2 < best]
        for i, a in enumerate(strip):
            for b in strip[i + 1 : i + 8]:
                if (b[1] - a[1]) ** 2 >= best:
                    break
                best = min(best, squared(a, b))
        return best, by_y

    return search(0, len(by_x))[0]
```

Sorted by x and split in two, each half's closest pair comes from the same function, and the only pairs left are across the split. A pair across it that's closer than either half's best, at a distance d, has both its points within d of the line between the halves, the strip, and its two points within d of each other in y. Sorted by y, a point in the strip can only be that close to one of the next 7: the points within d above it lie in a box d high and 2d wide, and points of the same half are at least d apart, so at most 4 of each half fit in it. Each call hands back its points sorted by y, merged from its halves' with `heapq.merge`, so the search takes time in proportion to n log n.

Checking every pair is the slow way: {% $fig.pairs %} pairs for the longest test. Sorting by x and comparing each point with those after it until the gap in x reaches d checks every pair too when the points share an x, as the tests' points along one line do.
