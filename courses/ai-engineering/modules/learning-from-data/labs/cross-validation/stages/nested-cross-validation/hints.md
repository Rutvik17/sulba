For each outer `(fit, held)`, `choose(X[fit], y[fit], folds(mixes[fit], k, seed), degrees, penalties)` makes the choice without the held-out tests.

---

`fold_errors(features(X, degree), y, [(fit, held)], [penalty])[0, 0]` fits the chosen pair on the outer fit tests and measures it on the held-out ones.
