Bayes' rule moves the classifier's probability `$p$` from the share of pulsars it was fit on to another, through the odds:

```math
\frac{p'}{1 - p'} = \frac{p}{1 - p} \cdot \frac{\pi' / (1 - \pi')}{\pi / (1 - \pi)}
```

| Symbol | Meaning |
| --- | --- |
| `$p$` | The classifier's probability |
| `$\pi$` | The share of pulsars among the candidates it was fit on, {% $fig.train_share %} |
| `$\pi'$` | The share among the new candidates |
| `$p'$` | The probability among the new candidates |

At {% $fig.one_in %}, every candidate's odds are multiplied by {% $fig.odds_factor %}. Adding the logarithm of that factor to the classifier's log-odds, its `decision_function`, and taking the sigmoid avoids dividing by `$1 - p$` where `$p$` is close to 1.

The checks drew {% $fig.drawn %} candidates from the validation and test sets, {% $fig.drawn_pulsars %} of them pulsars. The classifier's own probabilities for them add up to {% $fig.own_sum %}, and the adjusted ones to {% $fig.adjusted_sum %}.

The adjustment keeps every candidate's place in the order, so the ROC curve and the follow-ups are the same; what moves is the probabilities and what a threshold flags. At {% $fig.threshold %}, the classifier's own probabilities flag {% $fig.own_flags %} of the drawn candidates, {% $fig.own_precision %} of them pulsars, and the adjusted ones flag {% $fig.adjusted_flags %}, {% $fig.adjusted_precision %} of them pulsars.

The adjustment assumes that pulsars and other candidates look the same in the new pointing as in the training set, and only how many there are of each has changed. If the candidates themselves change, with a new kind of interference say, no share can make up for it, and the classifier needs new labelled candidates.
