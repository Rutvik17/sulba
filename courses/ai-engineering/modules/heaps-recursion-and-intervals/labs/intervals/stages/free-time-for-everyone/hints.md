Merge everyone's busy times into one sorted stream. Where in that stream is a free time?

---

`heapq.merge(*schedules)` gives every busy time in order of start. Keep the latest end so far: a busy time that starts after it leaves a free time from that end to its start.
