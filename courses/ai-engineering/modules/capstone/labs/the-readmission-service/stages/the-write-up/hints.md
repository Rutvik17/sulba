An f-string writes each number in its format: `f"{mean:.3f}"`, `f"{share:.1%}"`, `f"{count:,}"`. A triple-quoted f-string holds the whole page.

---

The folds `cross_validated` uses come from `StratifiedKFold(5, shuffle=True, random_state=SEED).split(table, y)`. Score each fold's held-out stays with `auc(table.iloc[test], probabilities[test])`, and `summary` gives the mean and its error.

---

`calibration(y, probabilities)` makes ten groups, and the last is the tenth of stays rated highest.
