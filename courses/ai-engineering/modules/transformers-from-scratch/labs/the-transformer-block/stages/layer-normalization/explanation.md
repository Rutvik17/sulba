Layer normalization works on each token's vector alone: its mean and variance come from that vector's own numbers. So it does the same thing in training and in use, whatever else is in the batch, unlike batch normalization, which averages over the batch and keeps running estimates for use.

The variance divides by `$n$`, not `$n - 1$`, as `F.layer_norm` computes it, and `$\epsilon$` goes inside the square root, so a vector whose numbers are all equal gives 0 rather than a division by 0. GPT-2's `$\epsilon$` is {% $fig.eps %}.

The weight and the bias let the model undo the normalization where that helps: a weight of `$\sigma$` and a bias of `$\mu$` give the vector back. Each layer normalization holds `$2n$` parameters. GPT-2 small has {% $fig.norms %} of them, two in each of its {% $fig.layers %} blocks and one after the last, each {% $fig.width %} wide: {% $fig.params %} parameters in all.

The gradient flows through the mean and the variance too, so every number's output depends on every number of its vector. Autograd works that out from your operations, which is why your gradients match `F.layer_norm`'s.
