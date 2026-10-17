SGD takes the same learning rate for every weight, however large or small its gradients run. Adam gives each weight a step of its own size: it keeps a running average of each gradient, `$m$`, and of each gradient squared, `$v$`, and steps by their ratio, so that a weight whose gradients are steady moves by about the learning rate, whatever their size.

Write `Adam.step(grads)`, as `torch.optim.Adam` takes its steps. Count the step first, so that `$t$` is 1 at the first. Then, for a parameter `$\theta$` with gradient `$g$`:

```math
\begin{aligned}
g &\leftarrow g + \lambda \theta \\
m &\leftarrow \beta_1 m + (1 - \beta_1) g \\
v &\leftarrow \beta_2 v + (1 - \beta_2) g^2 \\
\hat{m} &\leftarrow m / (1 - \beta_1^t), \quad \hat{v} \leftarrow v / (1 - \beta_2^t) \\
\theta &\leftarrow \theta - \gamma \, \hat{m} / (\sqrt{\hat{v}} + \epsilon)
\end{aligned}
```

`$m$` and `$v$` start at 0, which pulls both averages toward 0 at first, and dividing by `$1 - \beta^t$` corrects for that. The weight decay `$\lambda$` goes into the gradient, as an L2 penalty, as PyTorch's Adam has it.

```
Adam(params, lr=0.001, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0)
optimizer.step(grads), changing each array in params in place
optimizer.t, optimizer.m and optimizer.v, the step count and each parameter's averages
```

The tests compare your steps with `torch.optim.Adam`'s on {% $fig.cases %} recorded cases in `references/steps.json`, one with gradients small enough that `$\epsilon$` matters.
