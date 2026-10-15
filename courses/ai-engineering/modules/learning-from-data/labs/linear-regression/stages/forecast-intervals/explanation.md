An interval is only as honest as the misses it is built from. On the hours a model was fitted to, its misses tend to be smaller than on hours it hasn't seen, so the checks hold back one training hour in five from the fit and measure the misses there.

Sort the sizes of those `$n$` misses. The interval reaches `$\hat{q}$` either side of each forecast, where `$\hat{q}$` is the size at rank `$k$`:

```math
k = \lceil (n + 1)(1 - \alpha) \rceil
```

| Symbol | Meaning |
| --- | --- |
| `$n$` | The hours held back |
| `$1 - \alpha$` | The coverage asked for |
| `$\lceil \cdot \rceil$` | Round up to a whole number |
| `$k$` | The rank of the miss size that sets `$\hat{q}$`, counting from the smallest |

The `$n + 1$` is the new hour. If the new hour is like the held-back ones, its miss is as likely to rank anywhere among the `$n + 1$` misses as any of theirs. So it lands at or below rank `$k$` with probability `$k/(n + 1)$`, which is at least `$1 - \alpha$`. When `$k$` is more than `$n$`, no held-back miss is large enough to promise that, and the interval has no end.

Worked example, the checks' 90% interval:

```math
k = \lceil (\fig{n_held} + 1) \times 0.9 \rceil = \lceil \fig{k_exact} \rceil = \fig{k}
```

The miss size at rank {% $fig.k_rank %} is {% $fig.q %} MW, so each interval is {% $fig.width %} MW wide, and {% $fig.inside %} of the {% $fig.n_test %} test hours fall inside theirs.

The promise holds over hours on average, not for every kind of hour. Split the test hours into quarters by temperature, and the share inside runs from {% $fig.inside_lowest %} in one quarter to {% $fig.inside_highest %} in another.
