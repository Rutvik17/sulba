A graph's nodes are `Node`s, each with a `value` and a list of `neighbours`, the nodes it links to. Links go one way, a node can link to itself, and a graph can have cycles. Write `copy_graph`:

```
copy_graph(node) -> the copy of node, in a copy of every node it reaches
```

The copy has a new `Node` for each node that `node` reaches through links, with the same value, linking to the copies of the same neighbours in the same order. No copy links to an original node. Copying `None` gives `None`.

```
1 → 2, 3      copy_graph(one) → 1' → 2', 3'
2 → 3                            2' → 3'
3 → 1                            3' → 1'
```

The tests' largest graph has {% $fig.nodes %} nodes in one long cycle.
