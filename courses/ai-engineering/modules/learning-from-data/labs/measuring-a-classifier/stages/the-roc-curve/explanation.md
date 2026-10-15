The ROC curve plots, at every threshold, the share of pulsars flagged against the share of other candidates flagged. Scores in a random order run along the diagonal; scores that put every pulsar first climb straight to (0, 1). The area under the curve, the AUC, adds up its trapezoids:

```math
\text{AUC} = \sum_{i=1}^{n} \left(\text{FPR}_i - \text{FPR}_{i-1}\right) \frac{\text{TPR}_i + \text{TPR}_{i-1}}{2}
```

| Symbol | Meaning |
| --- | --- |
| `$\text{TPR}_i$` | The share of pulsars scored at or above threshold `$i$` |
| `$\text{FPR}_i$` | The share of other candidates scored at or above it |
| `$n$` | The number of thresholds after `$\infty$` |

The area has a plain meaning. Pick a pulsar and another candidate at random: the AUC is the chance that the pulsar has the higher score, with a tie counting half. The test set holds {% $fig.pairs %} such pairs, {% $fig.test_pulsars %} pulsars times {% $fig.test_others %} other candidates, and the classifier puts the pulsar first in {% $fig.share_right %} of them: its AUC is {% $fig.auc %}.

So the AUC depends only on the order of the scores. The classifier's log-odds, or any other scores in the same order, give the same curve. Nor does the curve change with the share of pulsars among the candidates, since each rate counts within one class.

At a threshold of {% $fig.threshold %}, the classifier flags {% $fig.tp %} of the {% $fig.test_pulsars %} pulsars, a true positive rate of {% $fig.tpr %}, and {% $fig.fp %} of the {% $fig.test_others %} others, a false positive rate of {% $fig.fpr %}. Its answers are right for {% $fig.accuracy %} of the candidates, but calling every candidate something other than a pulsar would be right for {% $fig.always_no %}. When one class is this rare, accuracy says little about how well the classifier finds it.
