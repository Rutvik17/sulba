`x.mean(dim=-1, keepdim=True)` gives each vector's mean with a dimension of 1 in place of the last, so it broadcasts against `x`.

---

The variance divides by `$n$`: `(x - mean).pow(2).mean(dim=-1, keepdim=True)`. `x.var(dim=-1)` divides by `$n - 1$` unless told `correction=0`.

---

`torch.nn.Parameter(torch.ones(width))` makes a tensor the module registers as a parameter under the attribute's name.
