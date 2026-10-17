The office's network trains by gradient descent: each step moves every weight a little against its gradient. PyTorch puts that step in an optimizer, which a training loop calls after each backward pass, and which adds what training needs: momentum, Nesterov's momentum and weight decay. This lab builds PyTorch's optimizers in NumPy, starting with `torch.optim.SGD`.

Write `SGD.step(grads)`, which moves each array in `self.params` one step, given its gradient. For a parameter `$\theta$` with gradient `$g$`, PyTorch's SGD takes the step in this order, skipping weight decay when `$\lambda$` is 0 and momentum when `$\mu$` is 0:

```math
\begin{aligned}
g &\leftarrow g + \lambda \theta \\
b &\leftarrow g \text{ at the first step, } \mu b + (1 - \tau) g \text{ after it} \\
g &\leftarrow g + \mu b \text{ with Nesterov's momentum, } b \text{ without} \\
\theta &\leftarrow \theta - \gamma g
\end{aligned}
```

Here `$\gamma$` is the learning rate, `$\lambda$` the weight decay, `$\mu$` the momentum and `$\tau$` the dampening. The buffer `$b$`, the velocity, belongs to its parameter and lasts from step to step. Change each parameter in place, so that the network, which holds the same arrays, sees the step, and leave the gradients as they were.

```
SGD(params, lr=0.001, momentum=0.0, dampening=0.0, weight_decay=0.0, nesterov=False)
optimizer.step(grads), a gradient for each array in params, in the same order
optimizer.lr, read at every step, so that a schedule can change it between steps
```

The tests compare your steps with `torch.optim.SGD`'s on {% $fig.cases %} recorded cases, each a weight and a bias given a gradient at every step, in `references/steps.json`.
