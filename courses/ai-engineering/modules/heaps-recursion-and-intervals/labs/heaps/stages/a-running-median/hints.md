Keep the smaller half of the numbers apart from the larger half, with the halves' sizes never more than one apart. Where is the median then?

---

Keep the smaller half in a max-heap, with `heapq.heappush_max`, so its largest is at index 0, and the larger half in a min-heap, with `heapq.heappush`, so its smallest is. After each number, move one across if the sizes are more than one apart.
