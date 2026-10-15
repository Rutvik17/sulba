`mu1 - mu0` points the right way. Divide it by its length, with your `norm`, to make it length 1.

---

The midpoint is `(mu0 + mu1) / 2`. Subtract it from every row of `Z` by broadcasting, then take the dot product of each row with the direction: `(Z - midpoint) @ u`.
