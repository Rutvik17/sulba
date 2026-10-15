The reliability table in {% $fig.bins %} bins, for the test candidates:

| Bin | Candidates | Mean probability | Share of pulsars |
| --- | --- | --- | --- |
| {% $fig.from_0 %}–{% $fig.to_0 %} | {% $fig.count_0 %} | {% $fig.mean_0 %} | {% $fig.share_0 %} |
| {% $fig.from_1 %}–{% $fig.to_1 %} | {% $fig.count_1 %} | {% $fig.mean_1 %} | {% $fig.share_1 %} |
| {% $fig.from_2 %}–{% $fig.to_2 %} | {% $fig.count_2 %} | {% $fig.mean_2 %} | {% $fig.share_2 %} |
| {% $fig.from_3 %}–{% $fig.to_3 %} | {% $fig.count_3 %} | {% $fig.mean_3 %} | {% $fig.share_3 %} |
| {% $fig.from_4 %}–{% $fig.to_4 %} | {% $fig.count_4 %} | {% $fig.mean_4 %} | {% $fig.share_4 %} |

Nearly every candidate sits in one of the two end bins, where the mean probability and the share of pulsars are close. The bins between hold {% $fig.middle_count %} candidates, so each pulsar more or less moves their shares a long way, but together they lean one way: their probabilities expect {% $fig.middle_expected %} pulsars, and {% $fig.middle_found %} are there. Between the ends, the classifier is less sure than it should be. Reading a reliability table means reading its counts too.

Calibrated probabilities can be added up: the expected number of pulsars among some candidates is the sum of their probabilities. For the test set the classifier's add up to {% $fig.sum_1 %}, and it holds {% $fig.test_pulsars %} pulsars.

The Brier score measures the probabilities against what happened:

```math
\text{BS} = \frac{1}{N} \sum_{i=1}^{N} \left(p_i - y_i\right)^2
```

| Symbol | Meaning |
| --- | --- |
| `$p_i$` | The probability given to candidate `$i$` |
| `$y_i$` | 1 if candidate `$i$` is a pulsar, 0 if not |
| `$N$` | The number of candidates |

The classifier scores {% $fig.brier_1 %}. Giving every candidate the training set's share of pulsars would score {% $fig.always_brier %}.

A Brier score rewards a sharp ranking as well as calibration, so a lower score doesn't by itself mean better-calibrated probabilities. Training with each pulsar counted more than once shows it:

| Pulsar weight | Probabilities add up to | AUC | Brier score |
| --- | --- | --- | --- |
| {% $fig.weight_1 %} | {% $fig.sum_1 %} | {% $fig.auc_1 %} | {% $fig.brier_1 %} |
| {% $fig.weight_2 %} | {% $fig.sum_2 %} | {% $fig.auc_2 %} | {% $fig.brier_2 %} |
| {% $fig.weight_5 %} | {% $fig.sum_5 %} | {% $fig.auc_5 %} | {% $fig.brier_5 %} |
| {% $fig.weight_10 %} | {% $fig.sum_10 %} | {% $fig.auc_10 %} | {% $fig.brier_10 %} |

A weight of {% $fig.weight_2 %} scores a little lower than {% $fig.weight_1 %}, though its probabilities add up to {% $fig.sum_2 %} for {% $fig.test_pulsars %} pulsars. Counting each pulsar `$w$` times fits the classifier to candidates with `$w$` times as many pulsars for each other candidate, so its probabilities run high while its ranking barely moves. scikit-learn's `class_weight="balanced"` would weigh each pulsar here {% $fig.balanced %} times as much as each other candidate.
