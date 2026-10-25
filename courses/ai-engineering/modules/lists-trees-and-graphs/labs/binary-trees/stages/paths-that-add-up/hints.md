On the way down from the root, a path that ends at a node adds up to the running total at that node minus the running total just above the path's start.

---

Walk down keeping a count of each running total on the way from the root, starting with 0. At each node, the paths ending there that add up to `target` are the running totals above it equal to its own minus `target`. Count the node's own total while you walk below it, and take it back out on the way up.
