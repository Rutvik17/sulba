Your ROC curve has the counts: at threshold `i`, `tpr[i]` times the number of pulsars is the pulsars flagged, and `fpr[i]` times the number of other candidates the others flagged. Leave out its first point, at `np.inf`, and reverse the rest so the thresholds run lowest first.

---

With the arrays in that order, `recall[i] - recall[i + 1]` is the recall that threshold `i` adds over the next higher one.

---

For every candidate screened, a threshold flags `share * tpr` pulsars and `(1 - share) * fpr` other candidates. `np.divide` with `out` and `where` gives 1 where the two add up to nothing.
