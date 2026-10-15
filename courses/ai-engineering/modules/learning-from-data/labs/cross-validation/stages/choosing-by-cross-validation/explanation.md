One split's error depends on which mixes it happens to hold out, and with {% $fig.seeds %} different seeds it ranged widely. At degree 3, the RMSE each method gave:

| Penalty | One split | Five folds |
| --- | --- | --- |
| {% $fig.small_penalty %} | {% $fig.one_low_small %} to {% $fig.one_high_small %} MPa | {% $fig.five_low_small %} to {% $fig.five_high_small %} MPa |
| {% $fig.chosen_penalty %} | {% $fig.one_low_chosen %} to {% $fig.one_high_chosen %} MPa | {% $fig.five_low_chosen %} to {% $fig.five_high_chosen %} MPa |

`$\lambda = \fig{last_penalty}$` is the penalty the last lab's validation split chose. A smaller penalty leaves the model freer to follow the tests it is fit on, so another split gives another model as well as other mixes to score it on. Five folds hold out every mix once and average the folds, so no single fold decides the estimate.

The pairs each method chose, over the same seeds:

| Pair chosen | One split | Five folds |
| --- | --- | --- |
| Degree {% $fig.top_degree %}, `$\lambda = \fig{top_penalty}$` | {% $fig.one_top %} | {% $fig.five_top %} |
| Any other pair | {% $fig.one_other %} | {% $fig.five_other %} |
| Pairs chosen in all | {% $fig.one_pairs %} | {% $fig.five_pairs %} |

Cross-validation's choice depends on the shuffle less than one split's does, but it still depends on it. Every pair is scored on the same folds, so the comparison between them isn't moved by which pair drew the easier folds.
