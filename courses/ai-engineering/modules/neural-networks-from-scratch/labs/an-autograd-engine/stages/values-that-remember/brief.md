The office's network has a backward pass written by hand for each kind of layer. A new layer or loss would need another, worked out and checked before it could train. An autograd engine does that work: every value it computes remembers the values it was made from and how, and a result's backward pass follows those records back to everything it came from, by the chain rule. PyTorch's autograd works this way.

Write `Value`, a number that remembers. `a + b`, `a * b` and `exp(a)` each give a new `Value` that keeps the values it was made from, and a function, `_backward`, that adds the new value's gradient, times its derivative, to each of theirs. A number works on either side of `+` and `*`: `2 * a` and `a + 1` give Values too.

`topological_order(output)` lists every value `output` was made from, `output` among them, each after all the values it was made from. `backward()` sets the output's gradient to 1, then calls each value's `_backward` in the reverse of that order, so that every value has its whole gradient before it passes it on.

```
Value(data)
a + b, a * b, exp(a), with a number on either side of + and *
topological_order(output) -> a list of Values
output.backward(), setting .grad on every value output was made from
```

The tests compare your values and gradients with PyTorch's on {% $fig.cases %} random expressions saved in `references/scalars.json`, each of {% $fig.steps %} steps on {% $fig.inputs %} numbers.
