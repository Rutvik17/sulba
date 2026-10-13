A threshold turns probabilities into decisions: the clinic sends every sample with `$p \ge t$` for a biopsy. Precision is the share of the samples sent that are malignant. Recall is the share of the malignant samples that are sent.

```math
\text{precision} = \frac{TP}{TP + FP}
```

```math
\text{recall} = \frac{TP}{TP + FN}
```

| Symbol | Meaning |
| --- | --- |
| `$t$` | The threshold |
| `$TP$` | Malignant samples with `$p \ge t$`: sent, and malignant |
| `$FP$` | Benign samples with `$p \ge t$`: sent, but benign |
| `$FN$` | Malignant samples with `$p < t$`: missed |

Worked example, the test set at `$t = 0.5$` with the fixed screener's probabilities:

| | Sent, `$p \ge 0.5$` | Not sent, `$p < 0.5$` |
| --- | --- | --- |
| Malignant | `$TP = \fig{tp}$` | `$FN = \fig{fn}$` |
| Benign | `$FP = \fig{fp}$` | {% $fig.tn %} |

```math
\text{precision} = \frac{\fig{tp}}{\fig{tp} + \fig{fp}} = \fig{precision}
```

```math
\text{recall} = \frac{\fig{tp}}{\fig{tp} + \fig{fn}} = \fig{recall}
```

When nothing is sent, precision would be `$0/0$`, and `precision_recall` gives `0.0`.

Lowering `$t$` sends more samples, so recall never falls, and precision usually does. The clinic sets the recall it needs, and the best threshold is the highest one that reaches it, since it sends the fewest samples. To reach a recall of `$r$`, at least `$k$` of the `$P$` malignant samples must be sent:

```math
k = \lceil rP \rceil
```

| Symbol | Meaning |
| --- | --- |
| `$r$` | `min_recall` |
| `$P$` | The number of malignant samples |
| `$\lceil x \rceil$` | `$x$` rounded up to a whole number |

Sort the malignant samples' probabilities from highest to lowest: the threshold is the one at position `$k$`. Any higher threshold sends fewer than `$k$` of them.

Worked example, a recall of 0.98 on the test set's {% $fig.positives %} malignant samples:

```math
k = \lceil 0.98 \times \fig{positives} \rceil = \lceil \fig{r_times_p} \rceil = \fig{k}
```

Sorted from highest to lowest, position {% $fig.k %} holds {% $fig.threshold %}, the lowest of them. At that threshold the clinic sends {% $fig.sent %} samples, {% $fig.extra %} of them benign, so precision falls to {% $fig.precision_at_threshold %}.

Sorting `$n$` probabilities takes about `$n \log n$` steps, so `best_threshold` stays fast as the clinic's records grow. Trying every probability as a threshold and counting again each time takes about `$n^2$` steps: four times the samples take sixteen times as long.

`np.sort(p)` returns a sorted copy. `p.sort()` sorts the array it is given, so the clinic's own probabilities would change with every call.
