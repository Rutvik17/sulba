An engine of single numbers is too slow for the office's network. One batch of {% $fig.batch %} digits through its first layer takes {% $fig.values %} multiplications and additions, and as Values that is {% $fig.values %} records, each with a backward pass of its own in Python. Record whole arrays instead.

Write `Tensor`, which holds a NumPy array and remembers the tensors it was made from, as `Value` does. Its operations are NumPy's: `+`, `-` and `*` element by element, with broadcasting; `@`, the matrix product; `.T`; `sum` and `mean`, along an axis or over every element; and `exp`, `log`, `tanh` and `relu` element by element. Each gradient has the shape of its tensor.

Broadcasting uses one value many times: `X + b`, with `b` a single row, adds `b` to every row of `X`, so `b`'s gradient adds up the gradients of every row. Write `unbroadcast(grad, shape)`, which sums a gradient back to the shape of the tensor broadcasting stretched, and use it in `+` and `*`.

```
Tensor(array)
a + b, a - b, a * b, -a, a @ b, a.T
a.sum(axis=None, keepdims=False), a.mean(axis=None, keepdims=False)
a.exp(), a.log(), a.tanh(), a.relu()
out.backward(), for a tensor out holding a single number
unbroadcast(grad, shape) -> grad summed back to shape
```

`backward` is `Value.backward` for arrays, with the same `topological_order`. The tests compare your values and gradients with PyTorch's on {% $fig.cases %} expressions saved in `references/tensors.json`, the office's kind of network among them.
