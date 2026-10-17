A value can reach the output along more than one path, as `$a$` does twice in `$a \cdot a$`. The chain rule then adds a term for each path: the gradient of the output with respect to a value is the sum, over the values made from it, of their gradients times the derivative of each step.

```math
\frac{\partial L}{\partial a} = \sum_{v \text{ made from } a} \frac{\partial L}{\partial v} \, \frac{\partial v}{\partial a}
```

That is why every `_backward` adds with `+=`, and why the order matters: a value may pass its gradient on only once every value made from it has added its share. In topological order each value comes after everything it was made from, so in the reverse order it comes after everything made from it.

Each value's `_backward` runs once and does a few multiplications and additions, a small multiple of its step's own work, so a backward pass costs a few times the forward pass that recorded it, however many inputs there are. Finite differences would take two forward passes for every input.
