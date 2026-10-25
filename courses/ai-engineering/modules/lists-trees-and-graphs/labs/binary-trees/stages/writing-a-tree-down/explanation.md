```python
def serialise(root):
    tokens, waiting = [], [root]
    while waiting:
        node = waiting.pop()
        if node is None:
            tokens.append("#")
        else:
            tokens.append(str(node.value))
            waiting += [node.right, node.left]
    return " ".join(tokens)


def deserialise(text):
    tokens = iter(text.split())

    def build():
        token = next(tokens)
        if token == "#":
            return None
        node = Node(int(token))
        node.left = build()
        node.right = build()
        return node

    return build()
```

`serialise` writes the nodes in preorder, with `#` for each missing child, so a node's text is its value, then its left subtree's text, then its right's. `deserialise` reads it back in the same order: each call takes one token, and a value goes on to build its left subtree, then its right, just where their text begins. A tree of n nodes has n + 1 missing children, so its text has 2n + 1 tokens, each written and read once.

Taking each token with `tokens.pop(0)` instead of an iterator is the slow way, since each pop shifts every token after it. The largest test's {% $fig.nodes %} nodes make {% $fig.tokens %} tokens, which `pop(0)` would shift {% $fig.shifts %} times.
