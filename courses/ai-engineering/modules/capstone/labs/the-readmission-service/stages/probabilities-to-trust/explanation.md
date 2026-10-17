Each of the {% $fig.stays %} stays now has a probability from a model that never saw it. They add up to {% $fig.expected %} readmissions, and the stays had {% $fig.readmitted %}. Ranked into ten groups of about {% $fig.group %} stays each, the probabilities hold up group by group. The lowest group's mean probability is {% $fig.low_predicted %}, and {% $fig.low_observed %} of its stays came back. The highest group's is {% $fig.high_predicted %}, against {% $fig.high_observed %}. No group is more than {% $fig.gap %} points from its share, and the highest group reads a little higher than it should.

The out-of-fold probabilities matter. A model scored on the stays it learned from flatters itself: fitted to every stay and scored on the same stays, the model's Brier score is {% $fig.in_sample %}, against {% $fig.brier %} out of fold. Only the out-of-fold numbers say what new patients will see.

The Brier score is the mean squared gap between each probability and what happened:

```math
\text{Brier} = \frac{1}{n} \sum_{i=1}^{n} \left(p_i - y_i\right)^2
```

| Symbol | Meaning |
| --- | --- |
| `$p_i$` | The probability for stay `$i$` |
| `$y_i$` | 1 if the stay was readmitted, 0 if not |
| `$n$` | The number of stays |

The model's is {% $fig.brier %}. Giving every stay the same {% $fig.rate %} would score {% $fig.base %}. The gap looks small because most of the score comes from the rarity of readmissions: a stay that wasn't readmitted, given {% $fig.rate %}, adds that probability squared, and {% $fig.not_readmitted %} of the stays weren't. Read it against the base rate's, not against 0.

Calibration and ranking are separate questions. A model can rank well with probabilities all twice too high, or be calibrated and rank no better than chance. The service needs both: the ranking to choose whom to call, and the probabilities so the planners know what a call is worth.
