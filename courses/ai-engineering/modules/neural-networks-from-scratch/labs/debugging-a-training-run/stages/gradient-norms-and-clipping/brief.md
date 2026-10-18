A step of SGD moves each parameter by the learning rate times its gradient, so a batch with a large gradient takes a large step, and at a learning rate that's too high one such step can wreck the run. `torch.nn.utils.clip_grad_norm_` bounds every step. It measures the gradients' total norm, as if they were all one vector, and when that's above `max_norm` it scales all of them down by the same factor:

```math
\lVert g \rVert = \big\lVert (\lVert g_1 \rVert_p, \ldots, \lVert g_n \rVert_p) \big\rVert_p, \qquad g_i \leftarrow g_i \cdot \min\left( \frac{\text{max\_norm}}{\lVert g \rVert + 10^{-6}}, 1 \right)
```

The same factor for every gradient keeps the step's direction and shortens it. Write PyTorch's three functions, on lists of NumPy arrays:

```
get_total_norm(tensors, norm_type=2.0) -> the total norm, a float
clip_grads_with_norm_(grads, max_norm, total_norm) -> None, scaling each array in place
clip_grad_norm_(grads, max_norm, norm_type=2.0) -> the total norm before clipping
```

`norm_type` is `$p$`, and `float("inf")` gives the largest size of any entry. The tests compare your functions with PyTorch's on {% $fig.cases %} recorded cases in `references/clipping.json`. The chart trains the office's network with your clipping, at a learning rate too high for it.
