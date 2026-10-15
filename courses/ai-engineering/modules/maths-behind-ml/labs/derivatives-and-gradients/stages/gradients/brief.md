A model has many parameters, and its loss has a slope along each: together they make the gradient. Element `i` of the gradient of `f` at `x` is the derivative of `f` as element `i` of `x` alone changes, so a numerical gradient takes one central difference along each element in turn.

Write `numerical_gradient`. It must leave `x` as it was: move a copy, or add a step to a new array, rather than change `x` in place.

Then write `relative_error`, which compares two gradients whatever their size: the length of their difference as a share of the longer of the two. Two gradients of length 0 agree, with a relative error of 0.

```
numerical_gradient(f, x, h=1e-6) -> an array of the shape of x
relative_error(a, b) -> a number of 0 or more
```

The tests take the gradient of the distance from the clinic's first new sample to its nearest record, in all {% $fig.measurements %} measurements, and compare it with the exact gradient and with SciPy's `approx_fprime`.
