k-means finds groups near the centres it starts from, and other starts can end in other groups, some with a larger inertia. k-means++ spreads the starts out: it draws the first centre from the rows at random, and each next one with a chance in proportion to a row's squared distance to its nearest centre so far, so that a row far from every centre is likelier to be drawn. Running k-means from several starts and keeping the groups with the least inertia guards against an unlucky one.

How many groups the beans fall into is another question. A row's silhouette compares `$a$`, its mean distance to the other rows of its group, with `$b$`, its mean distance to the rows of the nearest other group:

```math
s = \frac{b - a}{\max(a, b)}
```

It is near 1 for a row well inside its group, and below 0 for a row nearer another group than its own. The rows' mean silhouette is higher for groups that are tight and far apart.

Write `plus_plus`, `best_of` and `silhouette`:

```
plus_plus(Z, k, rng) -> k starting centres, one to a row
best_of(Z, k, starts, rng) -> (labels, centres, inertia)
silhouette(Z, labels) -> the rows' mean silhouette
```

`plus_plus` draws the first centre's row with `rng.integers(len(Z))`, and each next one with `rng.choice(len(Z), p=...)`, the chances in proportion to each row's squared distance to its nearest centre drawn so far. `best_of` runs your `k_means` from `starts` starts drawn by `plus_plus` with `rng`, one after another, and returns the run with the least inertia, the first of equal ones. `silhouette` takes groups numbered from 0, each with at least two rows. Import `cdist` from `scipy.spatial.distance` at the top of `groups.py`: `cdist(Z, Z)` gives the distance between every two rows.

The chart groups the training beans into {% $fig.low_k %} to {% $fig.high_k %} groups, each the best of {% $fig.starts %} starts by scikit-learn's `KMeans`, and draws your silhouettes beside the share of beans in their group's commonest variety.
