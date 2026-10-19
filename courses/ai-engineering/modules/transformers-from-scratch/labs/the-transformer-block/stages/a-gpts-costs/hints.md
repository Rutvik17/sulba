For a width of `$n$`, a block's attention holds two layers, `qkv` with `$3n^2 + 3n$` parameters and `out` with `$n^2 + n$`; its MLP two, `fc` with `$4n^2 + 4n$` and `proj` with `$4n^2 + n$`; and it has two layer normalizations of `$2n$` each.

---

In a forward pass, each token goes through a block's four matrices, `$12n^2$` multiply-adds, and its scores and values take `$n$` multiply-adds for each of the `length` tokens, twice. The output layer takes `$n$` for each token of the vocabulary.

---

In the backward pass, each matrix multiply `$Y = XW$` takes two of the same size: one for the gradient of `$X$`, one for that of `$W$`.
