XGBoost grows each tree from two numbers for each call: the gradient and the hessian of its log loss, its first and second derivatives with respect to the call's log-odds. For a call with a share of yes `$p$` that said `$y$`, 1 for yes and 0 for no, they are `$g = p - y$` and `$h = p(1 - p)$`.

For the calls in a leaf, with sums `$G$` and `$H$`, XGBoost's weight is `$-G / (H + \lambda)$`, where `$\lambda$` is its `reg_lambda`. The gain it reports for splitting a leaf's calls into a left and a right part is

```math
\begin{aligned}
\text{gain} = {} & \frac{G_L^2}{H_L + \lambda} + \frac{G_R^2}{H_R + \lambda} \\
& - \frac{(G_L + G_R)^2}{H_L + H_R + \lambda}
\end{aligned}
```

Write `gradients`, `leaf_weight`, `split_gain` and `best_split`:

```
gradients(said_yes, share) -> (g, h), each row's gradient and hessian
leaf_weight(g, h, lam) -> the weight of a leaf of these rows
split_gain(g, h, left, lam) -> the gain of splitting the rows into left and the rest
best_split(X, g, h, lam, min_child_weight) -> (column, threshold, gain)
```

`share` holds each row's share of yes, and `left` is a boolean array. `best_split` tries each column and, as each threshold, each of its distinct values but the smallest, splitting the rows into those with `X[:, column] < threshold` and the rest. It skips a split that leaves either part with a sum of hessians below `min_child_weight`, and returns the split with the greatest gain: of equal gains, the first, columns in order and thresholds from smallest.

XGBoost starts every call at one share, its `base_score`. The tests read it from XGBoost's model, give it to your `gradients`, and compare your splits, gains and weights with the trees XGBoost grows.
