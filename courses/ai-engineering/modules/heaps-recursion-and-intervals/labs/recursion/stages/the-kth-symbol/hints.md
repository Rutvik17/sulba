Each symbol of a row is written by one symbol of the row before. Which one, and when is it the other way round?

---

Places `2i - 1` and `2i` of a row both come from place `i` of the row before: the first is the same symbol, and the second is flipped. So a place's parent is at `(place + 1) // 2`.
