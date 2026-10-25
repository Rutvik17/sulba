$F(2k)$ and $F(2k + 1)$ can be worked out from $F(k)$ and $F(k + 1)$. How many halvings take n down to 0?

---

$F(2k) = F(k)\,(2F(k + 1) - F(k))$ and $F(2k + 1) = F(k)^2 + F(k + 1)^2$. A function that returns the pair `F(n), F(n + 1)` can work it out from the pair for `n // 2`, taking every number mod `modulus` as it goes.
