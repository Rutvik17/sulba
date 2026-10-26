A binary search tree keeps every node's value greater than every value in its left subtree and less than every value in its right subtree, so no value appears twice. Write `is_search_tree`:

```
is_search_tree(root) -> whether the tree under root is a binary search tree
```

`root` is a `Node` or `None`, and an empty tree is a search tree. The tree `5` with children `3` and `8`, where `3` has the right child `6`, is not one: `6` is in `5`'s left subtree. The tests' largest tree has {% $fig.nodes %} nodes, and its deepest is {% $fig.levels %} levels down.
