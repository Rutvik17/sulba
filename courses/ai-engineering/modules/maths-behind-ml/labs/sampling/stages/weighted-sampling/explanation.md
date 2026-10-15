The running totals of the weights cut the range from 0 to their total into one stretch for each row, as long as the row's weight. A uniform number scaled by the total is equally likely to land anywhere in that range, so it lands in row `$i$`'s stretch with probability `$w_i / \sum_j w_j$`. `np.searchsorted` finds the stretch by binary search, in about {% $fig.steps %} steps for {% $fig.records %} records. Taking the first running total above the number puts a number that lands exactly on a boundary into the stretch that starts there, so a row of weight 0, whose stretch is empty, is never drawn.

Scaling the uniform number by the total keeps every draw inside the last stretch. Weights meant to add up to 1 do so only to within rounding: the running total of {% $fig.count %} weights of {% $fig.weight %} ends at {% $fig.tenths %}, the largest number `rng.random` gives. A uniform number compared with that total as it stands lands past the last row once in about `$\fig{odds}$` draws. NumPy's `Generator.choice` divides its running totals by the last one, which then is exactly 1.

With balanced weights, the {% $fig.malignant %} malignant records and the {% $fig.benign %} benign ones each hold half the total weight. A batch of {% $fig.size %} then holds {% $fig.half %} malignant records on average, against {% $fig.plain %} with equal weights, as the chart shows.

The plain mean of such a batch estimates the mean over records that are half malignant, not over the clinic's. Each draw is row `$i$` with probability `$p_i$`, so

```math
\begin{aligned}
\operatorname{E}\left[\frac{v_I}{n p_I}\right] &= \sum_i p_i \cdot \frac{v_i}{n p_i} \\
&= \frac{1}{n} \sum_i v_i
\end{aligned}
```

and the reweighted mean is right on average. With balanced weights, a malignant draw counts for {% $fig.malignant_counts %} of a record and a benign one for {% $fig.benign_counts %}. A loss weighted the same way trains on the clinic's mix of records on average, while its batches hold as many malignant records as benign ones.
