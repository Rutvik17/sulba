```python
def lowest_common_ancestor(root, a, b):
    if root is None or root is a or root is b:
        return root
    left = lowest_common_ancestor(root.left, a, b)
    right = lowest_common_ancestor(root.right, a, b)
    if left is not None and right is not None:
        return root
    return left if left is not None else right
```

Each call returns `None` when its subtree holds neither node. Otherwise it returns a node: the answer, once both have been found below it, or whichever of `a` and `b` it found. A node that hears from both children is the lowest common ancestor. A node that is `a` or `b` returns itself without looking below: if the other is below it, it's the answer, and if not, a node higher up hears from both sides. It's one walk: time in proportion to the nodes, and space for the tree's height.

Walking down from the root, and at each node searching its left subtree for both nodes to choose a way, also finds it. But each step down searches again nodes the step before searched, so it can take time in proportion to the nodes times the depth of the answer.
