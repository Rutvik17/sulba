Precision and recall count the flags two ways:

```math
\begin{aligned}
\text{precision} &= \frac{\text{TP}}{\text{TP} + \text{FP}} \\
\text{recall} &= \frac{\text{TP}}{\text{TP} + \text{FN}}
\end{aligned}
```

| Symbol | Meaning |
| --- | --- |
| `$\text{TP}$` | Pulsars flagged |
| `$\text{FP}$` | Other candidates flagged |
| `$\text{FN}$` | Pulsars not flagged |

At a threshold of {% $fig.threshold %}, the classifier flags {% $fig.flags %} test candidates, {% $fig.tp %} of them pulsars: a precision of {% $fig.precision %} and a recall of {% $fig.recall %}.

Average precision sums up the whole curve. Each threshold's precision `$P_n$` counts for the recall `$R_n - R_{n-1}$` it adds:

```math
\text{AP} = \sum_{n} \left(R_n - R_{n-1}\right) P_n
```

On the test set it is {% $fig.ap %}. Scores in a random order flag pulsars at about their share at every recall, so their average precision is about that share, {% $fig.test_share %}: {% $fig.random_ap %} over {% $fig.shuffles %} random orders. A random order's ROC AUC is a half whatever the share, while its average precision falls with the share.

Unlike the ROC curve, precision depends on how common pulsars are. Where a share `$\pi$` of the candidates are pulsars, a threshold flags `$\pi \, \text{TPR}$` pulsars and `$(1 - \pi) \, \text{FPR}$` other candidates for every candidate screened:

```math
\text{precision} = \frac{\pi \, \text{TPR}}{\pi \, \text{TPR} + (1 - \pi) \, \text{FPR}}
```

The same threshold, with the same rates, flags:

| Pulsars among the candidates | Precision at {% $fig.threshold %} |
| --- | --- |
| {% $fig.share_half %} | {% $fig.precision_half %} |
| {% $fig.test_share %}, as in the test set | {% $fig.precision %} |
| {% $fig.share_hundred %} | {% $fig.precision_hundred %} |
| {% $fig.share_thousand %} | {% $fig.precision_thousand %} |

Where pulsars are rarer, each one comes with more false alarms, though the classifier ranks the candidates just as well. A precision measured on candidates is only good for candidates with the same share of pulsars.
