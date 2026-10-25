A dict finds a key at once. What can keep the keys in the order they were used, so that moving one to the front and dropping the oldest take a step each?

---

Keep the keys in a doubly linked list, newest at one end, and the dict from each key to its node. A node can unlink itself from its two neighbours in one step.
