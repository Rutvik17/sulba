The slope of `$f$` along a vector `$v$` is the dot product of its gradient with `$v$`:

```math
\frac{d}{dt} f(x + t v) \Big|_{t = 0} = \nabla f(x) \cdot v
```

So two evaluations of `$f$`, a central difference along `$v$`, check the gradient's dot product with `$v$`, however many parameters there are. A wrong gradient `$g + e$` is off along `$v$` by `$e \cdot v$`, which is 0 only when `$v$` is at a right angle to `$e$`, and a random direction almost never is. Checking a few directions guards against an unlucky one. Along {% $fig.directions %} directions the check takes {% $fig.direction_evaluations %} evaluations of the loss, where checking each of the {% $fig.big_parameters %} parameters takes {% $fig.big_evaluations %}. SciPy's `check_grad` can check along a random direction too, and so can PyTorch's `gradcheck` in its fast mode.

The comparison needs a scale. Along a random direction, `$g \cdot v$` can be close to 0 even when `$g$` isn't, so measuring the difference against it alone can call a right gradient wrong. Against the gradient's length, the tolerance means the same thing at every scale. A fixed tolerance, such as `$\fig{tolerance}$`, fails a right gradient once the loss is large and passes a wrong one once it is small: with the loss `$\fig{small_scale}$` times as large, the assistant's mistake in tanh's slope moves the slope along each of the {% $fig.directions %} directions by at most `$\fig{largest_shift}$`.

A tolerance of `$\fig{tolerance}$` of the gradient's length still leaves room for the central difference's own error, which stage 1 put many digits lower, and catches a single parameter off by {% $fig.one_off %}.
