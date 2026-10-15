The gradient collects a function's partial derivatives, each the slope along one element with the rest held still:

```math
\nabla f(x) = \left( \frac{\partial f}{\partial x_1}, \ldots, \frac{\partial f}{\partial x_n} \right)
```

For a distance `$d(z) = \lVert z - r \rVert$`, element `$j$` is `$(z_j - r_j)/d$`, so the gradient is `$(z - r)/\lVert z - r \rVert$`, the vector of length 1 that points from the record to the sample. It is the direction in which the distance grows fastest, at 1 standard deviation of distance per standard deviation moved. For the first new sample, it pulls hardest along the {% $fig.top1_name %}, {% $fig.top1 %}, and the {% $fig.top2_name %}, {% $fig.top2 %}: the measurements in which the sample and the record differ most, as the chart shows.

A numerical gradient costs two evaluations of `$f$` for each element: {% $fig.evaluations %} for the {% $fig.measurements %} measurements, and twice as many as a model has parameters. SciPy's `approx_fprime` takes forward differences, one evaluation for each element and one at `$x$`. Here its gradient has a relative error of `$\fig{forward_error}$`, and yours, from central differences, `$\fig{central_error}$`.

Comparing two gradients needs a measure that doesn't depend on their size. The length of their difference, which SciPy's `check_grad` returns, is small for any small gradient, right or wrong. Divided by the longer gradient's length, it says how many digits agree at any scale: a relative error of `$10^{-8}$` is agreement to about 8 digits.
