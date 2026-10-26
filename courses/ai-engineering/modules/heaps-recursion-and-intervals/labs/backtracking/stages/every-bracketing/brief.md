Write `bracketings`:

```
bracketings(pairs) -> every balanced string of pairs ( and pairs ), in sorted order
```

A string of brackets is balanced when each `(` is closed by a `)` after it, and each `)` closes a `(` before it. `bracketings(3)` returns `["((()))", "(()())", "(())()", "()(())", "()()()"]`, and `bracketings(0)` returns `[""]`. The tests ask for up to {% $fig.pairs %} pairs.
