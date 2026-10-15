```python
def assign(Z, centres):
    distances = ((Z[:, np.newaxis, :] - centres[np.newaxis, :, :]) ** 2).sum(axis=2)
    return distances.argmin(axis=1)


def k_means(Z, centres):
    labels = assign(Z, centres)
    groups = range(len(centres))
    while True:
        centres = np.array([Z[labels == group].mean(axis=0) for group in groups])
        moved = assign(Z, centres)
        if np.array_equal(moved, labels):
            break
        labels = moved
    inertia = float(((Z - centres[labels]) ** 2).sum())
    return labels, centres, inertia
```

Started from {% $fig.k %} training beans drawn at random, k-means assigned the beans {% $fig.rounds %} times before none changed group, and the inertia fell in every round, to {% $fig.inertia %}. Neither step can raise it: joining its nearest centre can only shorten a bean's distance, and a group's mean is the point with the least sum of squared distances to its beans. And as there are only so many ways to group the beans, the rounds come to an end.

The groups it found, by their training beans:

| Beans | Commonest variety | Its share |
| --- | --- | --- |
| {% $fig.beans_0 %} | {% $fig.variety_0 %} | {% $fig.share_0 %} |
| {% $fig.beans_1 %} | {% $fig.variety_1 %} | {% $fig.share_1 %} |
| {% $fig.beans_2 %} | {% $fig.variety_2 %} | {% $fig.share_2 %} |
| {% $fig.beans_3 %} | {% $fig.variety_3 %} | {% $fig.share_3 %} |
| {% $fig.beans_4 %} | {% $fig.variety_4 %} | {% $fig.share_4 %} |
| {% $fig.beans_5 %} | {% $fig.variety_5 %} | {% $fig.share_5 %} |
| {% $fig.beans_6 %} | {% $fig.variety_6 %} | {% $fig.share_6 %} |

k-means groups the beans by distance, and knows nothing of their {% $fig.varieties %} varieties. Two groups are mostly {% $fig.twice %}, and none is mostly {% $fig.missing %}, whose beans fall into groups of other varieties.
