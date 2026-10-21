A grader is worth what its verdicts agree with people's. BEGIN holds replies that models wrote in conversations about a sentence from Wikipedia, each labelled by people by whether everything it says can be put down to the sentence. `data/begin.csv` holds {% $fig.dev %} of them for development and {% $fig.test %} for testing, each with its text as `context`, the reply, and its label, and `data/begin-grades.csv` the grader's sums of `Yes` and `No` for each, from which `risk` gives its score.

In `agreement.py`, write, with `labels` 1 where people found the reply says something its text doesn't and 0 where they found it doesn't, and verdicts and scores in the same order:

- `accuracy(labels, verdicts)`: the share of the replies the grader gives the people's label.
- `kappa(labels, verdicts)`: Cohen's kappa, how far the agreement goes past the agreement the two would reach by chance if each gave 1 at its own rate, as a share of the most it could go.
- `auc(labels, scores)`: the chance that a reply labelled 1 scores above one labelled 0, a tie counting half.
- `best_threshold(labels, scores)`: the score, of those given, at or above which a reply is called 1, that gives the highest kappa, and the lowest of them if several do.

```math
\kappa = \frac{p_o - p_e}{1 - p_e}, \qquad p_e = p_\ell\, p_v + (1 - p_\ell)(1 - p_v)
```

`$p_o$` is the accuracy, and `$p_\ell$` and `$p_v$` the shares of 1 among the labels and the verdicts. The tests compare your measures with scikit-learn's.

```
accuracy(labels, verdicts) -> float
kappa(labels, verdicts) -> float
auc(labels, scores) -> float
best_threshold(labels, scores) -> float
```
