`calculate_gain` is a lookup: an `if` for each nonlinearity, with `param` read only for `leaky_relu`, where it's the slope, and 0.01 when it's `None`.

---

`fans(shape)` gives `(inputs, outputs)`. Xavier's bound is `gain * math.sqrt(6 / (fan_in + fan_out))`, and the weight is `rng.uniform(-bound, bound, size=shape)`.

---

Kaiming's gain is `calculate_gain(nonlinearity, a)`, and its fan is `fan_in`, or `fan_out` when `mode` is `"fan_out"`.
