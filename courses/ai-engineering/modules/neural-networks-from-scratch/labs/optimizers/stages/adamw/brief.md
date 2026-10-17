Weight decay pulls every weight toward 0 a little at each step, so that the network keeps only the weights its loss needs. Added to the gradient, as your Adam adds it, the decay goes through Adam's averages and comes out divided by `$\sqrt{\hat{v}}$` like the rest of the step: a weight with large gradients is barely decayed, and with no gradient every weight moves by the learning rate, whatever its size. AdamW takes the decay out of the gradient and shrinks each weight directly, before Adam's step:

```math
\begin{aligned}
\theta &\leftarrow \theta - \gamma \lambda \theta \\
\theta &\leftarrow \theta - \gamma \, \hat{m} / (\sqrt{\hat{v}} + \epsilon), \text{ with } m \text{ and } v \text{ made from } g \text{ alone}
\end{aligned}
```

PyTorch's Adam does this when it's given `decoupled_weight_decay=True`, and `torch.optim.AdamW` is Adam with it on and a weight decay of {% $fig.decay %}. Add the flag to your Adam, and write `AdamW` the same way.

```
Adam(params, lr=0.001, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0, decoupled_weight_decay=False)
AdamW(params, lr=0.001, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.01)
```

The tests compare your steps with `torch.optim.AdamW`'s on {% $fig.cases %} recorded cases in `references/steps.json`, one with gradients of 0, where only the decay moves the weights.
