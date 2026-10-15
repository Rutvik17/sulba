`(f(x + h) - f(x)) / h` is the forward difference. The central one steps both ways and divides by the distance between its two points, `2 * h`.

---

`np.cbrt(np.finfo(np.float64).eps)` is `$\fig{cbrt_eps}$`. Multiply it by `max(1.0, abs(x))` for the step.
