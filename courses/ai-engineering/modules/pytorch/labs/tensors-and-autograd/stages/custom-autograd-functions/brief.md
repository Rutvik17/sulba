`F.cross_entropy` keeps its backward pass to itself. Write the loss again with a backward pass of your own: `CrossEntropy`, a `torch.autograd.Function` whose `forward` gives the mean cross-entropy of a batch's logits against its digits, and whose `backward` gives its gradient as your NumPy `cross_entropy` did, the softmax less 1 at each digit, over the batch's size.

`forward(ctx, logits, digits)` saves what the backward pass needs with `ctx.save_for_backward`. `backward(ctx, grad)` returns a gradient for each input of `forward`. For the logits, that's `grad`, the gradient flowing in from whatever used the loss, times the loss's own gradient. For the digits it's `None`, since they have none. `cross_entropy(logits, digits)` calls it through `CrossEntropy.apply`.

```
CrossEntropy.forward(ctx, logits, digits) -> loss
CrossEntropy.backward(ctx, grad) -> (dlogits, None)
cross_entropy(logits, digits) -> loss
```

The tests hold it to `F.cross_entropy`'s loss and gradient, and run `torch.autograd.gradcheck` on it, which compares the backward pass with finite differences of the forward pass.
