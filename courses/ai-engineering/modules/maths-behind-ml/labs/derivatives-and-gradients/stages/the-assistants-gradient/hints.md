The assistant checked its gradient numerically, but only at zero weights. Ask which parts of the gradient are 0 there, whatever the code says.

---

Compare each line of `gradient` with your `network_gradient`, and with the loss: every term of the loss needs its term in the gradient, the decay's included.

---

`np.exp(s)` overflows float64 once `s` passes {% $fig.overflow %}. Your `network_loss` works the same loss out another way.
