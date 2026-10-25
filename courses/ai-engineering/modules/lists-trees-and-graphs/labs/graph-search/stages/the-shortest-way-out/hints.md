The squares one step from the start are reached first, then the squares one step from those. Which order of visiting finds each square by its shortest way?

---

Visit squares in the order you reach them, from a queue: a `collections.deque`, adding at the back and taking from the front. Record each square's steps when you first reach it, and never add it again.
