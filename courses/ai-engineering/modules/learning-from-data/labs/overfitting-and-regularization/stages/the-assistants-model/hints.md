The assistant's tests check that `choose` returns a pair it tried, that the model gives a strength per test, and that the error is a number of MPa. Ask what the plant relies on: the model you validated, a choice made on mixes the fit never saw, and an error measured on mixes the model hasn't seen.

---

Read each line that fits or scores a model. Which tests does it fit on, which does it score on, and with what penalty?

---

scikit-learn's `Ridge` minimizes `||y - Xw||² + alpha * ||w||²`: a sum of squared errors, not a mean.
