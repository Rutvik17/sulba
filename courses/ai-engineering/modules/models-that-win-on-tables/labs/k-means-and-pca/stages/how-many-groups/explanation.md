```python
def plus_plus(Z, k, rng):
    centres = [Z[rng.integers(len(Z))]]
    nearest = ((Z - centres[0]) ** 2).sum(axis=1)
    while len(centres) < k:
        centres.append(Z[rng.choice(len(Z), p=nearest / nearest.sum())])
        nearest = np.minimum(nearest, ((Z - centres[-1]) ** 2).sum(axis=1))
    return np.array(centres)


def best_of(Z, k, starts, rng):
    best = None
    for _ in range(starts):
        found = k_means(Z, plus_plus(Z, k, rng))
        if best is None or found[2] < best[2]:
            best = found
    return best


def silhouette(Z, labels):
    members = labels[:, np.newaxis] == np.arange(labels.max() + 1)
    sums = cdist(Z, Z) @ members
    sizes = members.sum(axis=0)
    rows = np.arange(len(Z))
    within = sums[rows, labels] / (sizes[labels] - 1)
    means = sums / sizes
    means[rows, labels] = np.inf
    nearest = means.min(axis=1)
    return float(np.mean((nearest - within) / np.maximum(within, nearest)))
```

{% $fig.k %} groups of the training beans, from {% $fig.seeds %} seeds:

| Starts | Least inertia | Mean | Most |
| --- | --- | --- | --- |
| One, from rows drawn at random | {% $fig.rows_low %} | {% $fig.rows_mean %} | {% $fig.rows_high %} |
| One, by k-means++ | {% $fig.plus_low %} | {% $fig.plus_mean %} | {% $fig.plus_high %} |
| The best of {% $fig.best_of %} by k-means++ | {% $fig.best_low %} | {% $fig.best_mean %} | {% $fig.best_high %} |

One start of either kind ends in groups whose inertia differs by hundreds from seed to seed, and the best of {% $fig.best_of %} by less than 1. scikit-learn's `KMeans` keeps the best of `n_init` runs, and its default, `n_init="auto"`, runs a single k-means++ start.

The silhouette is highest at {% $fig.top %} groups, {% $fig.top_score %}, and falls to {% $fig.varieties_score %} at {% $fig.varieties %}, one group for each variety. More groups fit the varieties better: the share of beans in their group's commonest variety rises from {% $fig.top_share %} at {% $fig.top %} groups to {% $fig.varieties_share %} at {% $fig.varieties %} and {% $fig.high_share %} at {% $fig.high_k %}. The groups the measurements separate most cleanly are not the varieties people named, and how many groups to keep depends on what the groups are for.
