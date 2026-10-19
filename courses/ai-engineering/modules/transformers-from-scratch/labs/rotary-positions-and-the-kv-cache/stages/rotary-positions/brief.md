The reading app's stories will now come from Hugging Face's SmolLM2-135M, a model trained on {% $fig.trained_tokens %} tokens and small enough to run on the device. It is built as Meta's Llama 2 is, and differs from the app's GPT in four parts: rotary positions for learnt ones, RMSNorm for layer normalization, a SwiGLU MLP, and grouped-query attention, with fewer key and value heads than query heads. Its linear layers have no biases. This stage builds rotary positions.

The app's GPT adds a learnt vector for each position to each token's vector, so it can't read past its context, and the score between two tokens depends on where each one is, not only on how far apart they are. SmolLM2 turns each head's queries and keys instead. A head of {% $fig.dim %} numbers holds {% $fig.pairs %} pairs, each number of its first half with the number {% $fig.pairs %} places after it, and at position `$m$` pair `$i$` turns through the angle `$m\theta_i$`:

```math
\theta_i = b^{-2i/d}, \qquad
\begin{pmatrix} x'_i \\ x'_{i+d/2} \end{pmatrix} =
\begin{pmatrix} \cos m\theta_i & -\sin m\theta_i \\ \sin m\theta_i & \cos m\theta_i \end{pmatrix}
\begin{pmatrix} x_i \\ x_{i+d/2} \end{pmatrix}
```

where `$d$` is the head's width and SmolLM2's base `$b$` is {% $fig.theta %}.

In `rope.py`, write:

- `frequencies(dim, theta)`, the angle each pair turns through a position, `$\theta_i$` for `$i$` from 0 to `dim // 2 - 1`, as a float64 tensor.
- `rotate(x, positions, theta)`, `x` (..., length, dim) with each row turned by the angles of its position: row `t` by `positions[..., t]`. The leading dimensions of `positions` broadcast with `x`'s, so each story in a batch can have positions of its own. Keep `x`'s dtype.

```
frequencies(dim, theta) -> tensor (dim // 2,)
rotate(x, positions, theta) -> tensor shaped like x
```

The tests compare your rotation with transformers' Llama at positions up to {% $fig.last %}, the last of SmolLM2's {% $fig.context %}.
