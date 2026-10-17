Over stage 3's folds, the three candidates compare like this, against the {% $fig.readmitted %} readmissions that came back:

| Model | Mean AUC | Readmissions expected |
| --- | --- | --- |
| Logistic regression | {% $fig.lr %} ± {% $fig.lr_error %} | {% $fig.lr_expected %} |
| Boosted trees | {% $fig.trees %} ± {% $fig.trees_error %} | {% $fig.trees_expected %} |
| Weighted logistic regression | {% $fig.weighted %} ± {% $fig.weighted_error %} | {% $fig.weighted_expected %} |

Only the logistic regression passes all three checks.

The bar asks a model to come within one standard error of the logistic regression, and the boosted trees fall short of it, though not by much. Fold by fold, the logistic regression is ahead by {% $fig.gain %} on average, give or take {% $fig.gain_error %}, and the trees win {% $fig.folds_trees_ahead %} of the {% $fig.folds %} folds. That's no proof the trees are worse, but nothing suggests they're better, and a model that ranks no better isn't worth what it adds: trees to fit, keep and explain, where the logistic regression has one weight for each input. Their probabilities add up well, to {% $fig.trees_expected %}.

The weighted logistic regression ranks the stays as the logistic regression does, at {% $fig.weighted %}, yet its probabilities add up to {% $fig.weighted_expected %} readmissions. `class_weight="balanced"` weighs each class by the number of samples over the number of classes times the class's count. Each readmitted stay here counts as much as {% $fig.weight %} stays that weren't, so the readmitted stays together weigh as much as the rest, and the model learns as if as many stays came back as didn't. Its ranking barely moves, but its probabilities answer for that world: the tenth of stays it rates highest average {% $fig.weighted_top %}, and {% $fig.weighted_top_observed %} of them came back.

The model that ships is fitted on every stay. Cross-validation measured the pipeline: each fold's model learned from the other folds' stays and was then set aside. `chosen` fits a new model from `make_chosen()` on all {% $fig.stays %}.

The ID mapping lists {% $fig.codes %} admission types, admission sources and discharges other than a death or hospice care, and {% $fig.unseen %} of them are on no stay in the extract. By default, a one-hot encoder raises an error when it meets a category it didn't learn. With `handle_unknown="ignore"`, as all three candidates have, that category's columns are all zeros instead, and the model answers from the stay's other inputs.
