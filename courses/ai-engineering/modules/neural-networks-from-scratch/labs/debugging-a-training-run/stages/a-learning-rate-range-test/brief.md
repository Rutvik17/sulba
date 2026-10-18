A run's learning rate has to be right: too low and the loss barely moves, too high and it jumps about or blows up. A range test finds the useful range in one short run. Start the network at a tiny learning rate, raise it a little at every step, by the same factor each time, up to a large one, and record the loss. It stays flat while the steps are too small to matter, falls once they're large enough to learn, and turns up when they're too large.

One batch's loss is noisy, so record it smoothed: an average that keeps `$\beta$` of itself at each step and takes in `$1 - \beta$` of the new loss, divided by `$1 - \beta^t$` at step `$t$`, as Adam's averages are, since it starts at 0:

```math
a_t = \beta a_{t-1} + (1 - \beta) \ell_t, \qquad \hat{a}_t = \frac{a_t}{1 - \beta^t}
```

Stop at the step whose smoothed loss passes `stop` times the lowest so far, or isn't a number: by then the steps are far too large.

```
range_test(params, batches, lr_min, lr_max, beta=0.98, stop=4.0, loss_and_grads=loss_and_grads)
    -> (the learning rates, the smoothed loss before each step), up to the step it stops at
lowest(lrs, smoothed) -> the learning rate at the lowest smoothed loss
```

`batches` holds an `(X, digits)` pair for each step, and the learning rates are `np.geomspace(lr_min, lr_max, len(batches))`. `range_test` takes its steps with a copy of the network, as `learn_by_heart` does. The chart runs your range test on the office's network.
