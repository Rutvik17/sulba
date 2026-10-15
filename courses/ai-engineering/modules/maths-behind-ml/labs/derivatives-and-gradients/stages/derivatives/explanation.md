Taylor's theorem says how far each slope falls from the derivative. Around `$x$`,

```math
f(x + h) = f(x) + h f'(x) + \frac{h^2}{2} f''(x) + \frac{h^3}{6} f'''(x) + \cdots
```

so a forward difference is off by about `$\frac{h}{2} f''(x)$`, in proportion to `$h$`. In a central difference the `$h^2$` terms cancel, and it is off by about `$\frac{h^2}{6} f'''(x)$`. Halve the step, and the forward difference's error halves while the central difference's falls to a quarter. This is the truncation error, and it shrinks with the step.

Rounding grows as the step shrinks. A float64 holds `$f(x)$` only to within about machine epsilon, `$\varepsilon = \fig{eps}$`, times its size. Subtracting two nearby values of `$f$` keeps that absolute error while the difference itself shrinks with `$h$`, so after dividing by `$h$`, rounding adds about `$\varepsilon \lvert f(x) \rvert / h$`. The best step balances the two: near `$\sqrt{\varepsilon} = \fig{sqrt_eps}$` for a forward difference and near `$\sqrt[3]{\varepsilon} = \fig{cbrt_eps}$` for a central one, when `$f$` and its derivatives are of everyday size. SciPy's `approx_fprime` takes forward differences with a step of `$\sqrt{\varepsilon}$` unless told otherwise, and PyTorch's `gradcheck` takes central differences with a step of `$\fig{torch_step}$`.

The chart shows both errors for the distance from the clinic's first new sample to its nearest record, as the sample's worst texture changes. The sample's worst texture is {% $fig.gap %} standard deviations below the record's and the distance is {% $fig.distance %}, so the derivative is {% $fig.exact %}: the gap over the distance. The forward difference comes closest at a step of `$10^{\fig{fwd_power}}$`, off by `$\fig{fwd_best}$`, and the central one at `$10^{\fig{cen_power}}$`, off by `$\fig{cen_best}$`. Below those steps rounding takes over, and the errors climb back up and jitter.

A fixed step can't suit every `$x$`. For `$x^3$` at `$\fig{far}$`, a central difference with a step of `$\fig{torch_step}$` is off by `$\fig{fixed_error}$` of the derivative, since the step changes `$x$` only in its last few digits. With the step scaled to `$\lvert x \rvert$`, it is off by `$\fig{scaled_error}$`.
