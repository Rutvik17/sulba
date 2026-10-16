Keep two bounds, `low` and `high`, so that every number before `low` is smaller than `value` and every number from `high` on is not.

---

Look at the number in the middle of the bounds. If it's smaller than `value`, the answer is after it; otherwise the middle could be the answer, so keep it inside.
