A copy's `random` must point to the copy of a node. How could you find a node's copy in one step?

---

Make every copy first, kept in a dict by the original node, then set each copy's `next` and `random` from the dict.
