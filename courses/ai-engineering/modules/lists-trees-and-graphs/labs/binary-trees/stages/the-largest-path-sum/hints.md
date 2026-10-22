A path has a highest node, and goes down at most one way on each side of it. What's the best way down from a node, if it can stop anywhere?

---

In one walk from the bottom up, work out each node's best way down: its value plus its better child's, taking nothing from a child whose best is below 0. The best path whose highest node is this one adds both children's best ways down, each at least 0, to its value.
