Write the nodes in preorder, each node before its subtrees, with a mark where a child is missing. Is that enough to rebuild the shape?

---

Read the marks and values back in the same order through an iterator. Each call takes the next one; a value makes a node, whose left subtree is built next, then its right.
