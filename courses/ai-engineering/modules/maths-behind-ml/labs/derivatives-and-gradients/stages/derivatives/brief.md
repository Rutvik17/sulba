Start `gradients.py`. A model learns by following derivatives, and code that works one out is checked against an estimate taken from the function itself. The derivative of `f` at `x` is the limit of the slope between two points as they close in on `x`. A finite difference takes that slope with a small step `h` instead.

Write `forward_difference`, the slope from `x` to `x + h`, and `central_difference`, the slope from `x - h` to `x + h`.

Then write `derivative`, a central difference with a step chosen for `x`: the cube root of float64's machine epsilon, `np.finfo(np.float64).eps`, times `|x|` when `|x|` is above 1, so that the step stays a share of `x` however large `x` is.

```
forward_difference(f, x, h) -> a number
central_difference(f, x, h) -> a number
derivative(f, x) -> a number
```

The tests use polynomials, whose derivatives are known exactly, and the distance from the clinic's first new sample to its nearest record as the sample's worst texture changes, compared with SciPy's `scipy.differentiate.derivative`.
