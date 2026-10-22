Ask each subtree whether it holds `a` or `b`. Which node is the first to hear yes from both sides?

---

Walk the tree once, bottom up. Each call returns `None` when its subtree holds neither node, and otherwise a node: `a`, `b` or, once both are found below it, the answer. A node that is `a` or `b` can return itself without looking below.
