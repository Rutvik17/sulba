For a width of `$n$`, `$L$` blocks, a vocabulary of `$V$`, a context of `$T$` and a story of `$\ell$` tokens:

```math
\begin{aligned}
\text{parameters} &= V n + T n + L\,(12 n^2 + 13 n) + 2 n \\
\text{forward} &= L\,(12 n^2 + 2 \ell n) + V n \\
\text{training} &= 3 \cdot \text{forward}
\end{aligned}
```

GPT-2 small, on its whole context of {% $fig.context %} tokens, takes {% $fig.small_forward %} multiply-adds a token to read and {% $fig.small_training %} to learn from. Most of a forward pass is a multiply-add for each parameter in the blocks and the output layer, which is why a model's cost to read a token is about its size, and its cost to learn from one about three times that. The position embeddings, the layer normalizations' parameters and the biases cost no multiply-adds, and attention adds `$2 L \ell n$`, which grows with the story.

The backward pass of each matrix multiply takes two of the same size, one for each input's gradient, so training takes three times the forward pass. That holds for the first layer too, since the gradient flows back to the embeddings.
