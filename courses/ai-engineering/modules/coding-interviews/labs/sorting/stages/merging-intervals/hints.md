Once the intervals are sorted by start, any interval that overlaps the ones before it overlaps the last of them merged so far.

---

Sort, then go through the intervals keeping a list of merged ones. An interval that starts at or before the last merged one ends extends it; any other starts a new one.
