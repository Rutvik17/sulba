import heapq
from collections import Counter


def reorganized(text):
    counts = [(count, letter) for letter, count in Counter(text).items()]
    heapq.heapify_max(counts)
    letters, held = [], None
    while counts:
        count, letter = heapq.heappop_max(counts)
        letters.append(letter)
        if held:
            heapq.heappush_max(counts, held)
        held = (count - 1, letter) if count > 1 else None
    return "".join(letters) if held is None else ""
