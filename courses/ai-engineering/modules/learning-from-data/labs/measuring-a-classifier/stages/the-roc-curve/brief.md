Start `metrics.py`. A radio survey's pipeline turns up candidates, and almost all of them are interference or noise rather than pulsars. The survey's classifier gives each candidate a probability of being a pulsar, and the astronomers will check the candidates at or above a threshold. Before choosing one, measure how well the probabilities put the pulsars first.

At a threshold, the true positive rate is the share of pulsars scored at or above it, and the false positive rate the share of other candidates. Lowering the threshold from above every score to the lowest one traces the ROC curve from (0, 0) to (1, 1).

Write `roc_curve`, which returns the false positive rates, the true positive rates and their thresholds, as scikit-learn's `roc_curve` does with `drop_intermediate=False`. The first threshold is `np.inf`, where nothing is flagged, and then come the distinct scores from highest to lowest. Candidates with the same score cross the threshold together.

Then write `roc_auc`, the area under that curve by the trapezoid rule, as scikit-learn's `roc_auc_score` gives it.

```
roc_curve(y, scores) -> (fpr, tpr, thresholds)
roc_auc(y, scores) -> the area under the curve
```

`y` is 1 for a pulsar and 0 for any other candidate. The tests score the {% $fig.test %} test candidates with the survey's classifier: scikit-learn's `LogisticRegression` on standardized measurements, fit on the {% $fig.train %} training candidates.
