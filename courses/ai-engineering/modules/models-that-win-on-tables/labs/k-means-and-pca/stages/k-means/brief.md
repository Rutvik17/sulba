Principal components describe how the beans vary. k-means looks for groups among them, without their varieties. It starts from k centres and repeats two steps:

1. each row joins the group of its nearest centre, by straight-line distance;
2. each centre moves to the mean of its group's rows.

Once a round leaves every row in the group it was in, the groups are those k-means finds. Their inertia is the sum of each row's squared distance to its group's centre.

Write `assign` and `k_means`:

```
assign(Z, centres) -> each row's nearest centre, as the index of its row in centres
k_means(Z, centres) -> (labels, centres, inertia)
```

`assign` gives a row as near two centres the first of them. `k_means` assigns the rows to the centres it's given, then moves the centres and assigns again until no row changes group. It returns each row's group, the groups' centres and their inertia, and leaves the centres it was given as they were. The tests start it from centres none of whose groups is ever left empty, and compare it with scikit-learn's `KMeans` started from the same centres.
