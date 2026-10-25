The list is sorted already. Which intervals come wholly before the new one, which overlap it, and which come wholly after?

---

Copy the intervals that end before `new` starts. Then, while an interval starts no later than the new one ends, merge it in, widening the new interval's ends. Add the merged interval, then the rest.
