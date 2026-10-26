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
