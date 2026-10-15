The clinic's next network has {% $fig.big_hidden %} hidden units and {% $fig.big_parameters %} parameters. A numerical gradient takes two evaluations of the loss for each parameter: {% $fig.big_evaluations %} passes over the {% $fig.records %} records, too many to check the gradient before every training run.

Ship `directional_slope`, `f`'s slope at `x` along a vector `v` by a central difference, and `gradient_agrees`, which says whether `gradient(x)` gives `f`'s slope along random directions drawn from `rng`. The slope of `f` along `v` is the dot product of its gradient with `v`, and a central difference finds it with two evaluations, however many parameters there are.

```
directional_slope(f, x, v, h=1e-6) -> a number
gradient_agrees(f, gradient, x, rng) -> True or False
```

`gradient_agrees` must find a wrong gradient, even one wrong in a single parameter, and accept a right one whatever the size of the loss. It must leave `x` as it was, and check {% $fig.big_parameters %} parameters in under a second.

There are no hints. The tests are hidden: you see which pass, but not their inputs. Four more checks decide whether it ships.
