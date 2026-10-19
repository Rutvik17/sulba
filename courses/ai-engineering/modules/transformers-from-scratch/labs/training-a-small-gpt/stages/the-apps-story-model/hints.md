A run's multiply-adds are its tokens times three times a forward pass of one token, as you worked out in The transformer block lab: `$3(12 L d^2 + 2 L n d + V d)$` for `$L$` blocks of width `$d$`, a context of `$n$` and a vocabulary of `$V$`.

---

The budget fixes the product of the model's cost a token and the tokens it reads. Halve the cost a token and the model reads twice as many.

---

The peak learning rate matters as much as the size: compare a few on short runs before the full one. Keep the warm-up short, a few percent of the steps.
