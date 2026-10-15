Each pair's cross-validated error carries some luck in how its folds fell. The lowest of {% $fig.pairs_tried %} is likely to be a pair whose luck ran good, so it reads lower than the error that pair makes on new mixes. Choosing is part of fitting the model, so its effect can only be measured on mixes the choice never saw. Nested cross-validation makes the choice afresh in each outer fold, on that fold's fit tests, and scores the chosen pair on the fold's held-out mixes.

| Estimate | RMSE |
| --- | --- |
| The chosen pair's cross-validated error | {% $fig.best %} MPa |
| Nested cross-validation | {% $fig.nested %} MPa |
| The test set, refit on every record | {% $fig.test %} MPa |

Of the 5 outer folds, {% $fig.outer_top %} chose degree {% $fig.chosen_degree %} with `$\lambda = \fig{chosen_penalty}$`, the pair chosen on all the records. The others chose `$\lambda = \fig{other_1}$` and `$\lambda = \fig{other_2}$`, and the nested estimate counts what those choices cost too. It measures the procedure, choosing by five folds and then fitting, on records like the plant's, rather than the one model fit on all of them.

The test set agrees with the nested estimate more closely than with the chosen pair's own score. It was used once, after the choice, so nothing was chosen to suit it.

Nested cross-validation fits {% $fig.nested_fits %} models where one cross-validation fits {% $fig.cv_fits %}: each outer fold repeats the whole search, then fits its choice once.
