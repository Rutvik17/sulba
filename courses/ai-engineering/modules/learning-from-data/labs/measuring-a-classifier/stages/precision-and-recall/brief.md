The astronomers will check every candidate the classifier flags, so what the checks cost depends on how many of the flags are pulsars. Precision is the share of flagged candidates that are pulsars, and recall, the true positive rate, the share of pulsars flagged.

Write `pr_curve`, which returns the precision and recall at every threshold, as scikit-learn's `precision_recall_curve` gives them: the thresholds are the distinct scores, lowest first, and after the last of them come a precision of 1 and a recall of 0. Then write `average_precision`, which weights each threshold's precision by the recall it adds over the next higher threshold, as scikit-learn's `average_precision_score` does.

Precision also depends on how common pulsars are among the candidates. Write `precision_at`, which gives the precision of a threshold's flags from its true and false positive rates, among candidates of which `share` are pulsars. Where nothing is flagged, it gives 1.

```
pr_curve(y, scores) -> (precision, recall, thresholds)
average_precision(y, scores) -> float
precision_at(share, tpr, fpr) -> the precision, for one threshold's rates or arrays of them
```

The {% $fig.test %} test candidates are {% $fig.test_share %} pulsars.
