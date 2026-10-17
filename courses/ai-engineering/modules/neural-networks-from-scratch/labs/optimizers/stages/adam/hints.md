Add 1 to `self.t` once at the top of `step`, before the loop, since every parameter shares the step count.

---

Keep the averages in `self.m[number]` and `self.v[number]`: `beta1 * self.m[number] + (1 - beta1) * grad`, and the same with `beta2` and `grad**2`.

---

The corrected averages are `self.m[number] / (1 - beta1**self.t)` and `self.v[number] / (1 - beta2**self.t)`. `eps` goes outside the square root: `np.sqrt(v_hat) + self.eps`.
