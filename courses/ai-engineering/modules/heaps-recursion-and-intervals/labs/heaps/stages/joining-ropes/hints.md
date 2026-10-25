A rope's length is paid again in every join it's part of. Which ropes should be in the fewest joins, and which two should go first?

---

`heapq` keeps the shortest rope at index 0: `heappop` takes the two shortest, and `heappush` puts the joined rope back among the others.
