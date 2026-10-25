Walk the list once. At each node, what do you need to remember before you point its `next` the other way?

---

Keep the part already reversed, starting from `None`. Each node in turn goes on its front: save its `next`, point it at the reversed part, and move on.
