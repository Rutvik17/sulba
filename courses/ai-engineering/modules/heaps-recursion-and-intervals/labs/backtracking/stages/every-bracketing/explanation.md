```python
def bracketings(pairs):
    found, chosen = [], []

    def extend(opened, closed):
        if closed == pairs:
            found.append("".join(chosen))
            return
        if opened < pairs:
            chosen.append("(")
            extend(opened + 1, closed)
            chosen.pop()
        if closed < opened:
            chosen.append(")")
            extend(opened, closed + 1)
            chosen.pop()

    extend(0, 0)
    return found
```

A string is balanced when no start of it closes more brackets than it opens, and the whole of it closes all it opens. So the search adds `(` while fewer than `pairs` are open, and `)` while fewer are closed than opened, and every string it finishes is balanced: none is built and thrown away. `(` comes before `)`, so trying it first gives the strings in sorted order.

There are $\frac{1}{n+1}\binom{2n}{n}$ balanced strings of n pairs, the Catalan numbers: {% $fig.count %} for the tests' {% $fig.pairs %} pairs. Writing out every string of {% $fig.length %} brackets and keeping the balanced ones is the slow way: {% $fig.strings %} strings for those {% $fig.count %}.
