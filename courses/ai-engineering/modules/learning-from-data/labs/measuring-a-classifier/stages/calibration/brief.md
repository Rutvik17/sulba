The astronomers will also plan with the probabilities themselves: how many pulsars to expect in a night's candidates, and how much to trust one candidate's chance. That works only if the probabilities are calibrated, so that of the candidates given about 0.8, about 80% are pulsars.

Write `reliability`, which bins the probabilities into `bins` bins of equal width from 0 to 1 and returns, for each bin that holds any, the share of its candidates that are pulsars and their mean probability, in that order, as scikit-learn's `calibration_curve` does with `strategy="uniform"`. A bin holds the probabilities above its lower edge up to and including its upper edge, and the first bin holds 0 too.

Then write `brier`, the Brier score: the mean squared difference between each probability and what happened, 1 for a pulsar and 0 for any other candidate, as scikit-learn's `brier_score_loss` gives it.

```
reliability(y, p, bins=10) -> (share of pulsars, mean probability), one of each per bin
brier(y, p) -> float
```

The test set holds {% $fig.test_pulsars %} pulsars.
