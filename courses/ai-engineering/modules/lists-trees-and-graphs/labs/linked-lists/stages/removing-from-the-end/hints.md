If one pointer starts `n` nodes ahead of another and both move together, where is the second when the first reaches the end?

---

Start both at a node before the head, so that the one behind stops at the node before the one to remove, and removing the head is no special case.
