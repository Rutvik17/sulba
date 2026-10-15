A new supplier sends the seed company its harvest without the varieties. Before the beans are named, the company wants to know how they differ: which ways their {% $fig.measurements %} measurements vary together, and how few numbers say most of what the measurements say.

The measurements move together: a long bean has a long perimeter and a large area. Along a direction, each bean has a score, the dot product of its scaled measurements with the direction. The first principal component is the direction of length 1 whose scores vary most among the training beans, and each next one, at right angles to those before it, the direction with the most variance left. They are the eigenvectors of the covariance matrix of the scaled measurements, and each one's eigenvalue is the variance of the scores along it.

Write `components` and `project`:

```
components(Z) -> (variances, directions)
project(Z, directions) -> each row's score on each direction
```

`components` takes scaled measurements, a row for each bean, and gives the eigenvalues of their covariance matrix from the largest down, and the eigenvectors in the same order, one to a row of `directions`. `np.cov(Z, rowvar=False)` gives the covariance matrix, dividing by the number of rows less one, and `np.linalg.eigh` gives its eigenvalues from the smallest up and its eigenvectors as columns. An eigenvector turned around is an eigenvector too: turn each one so that its entry farthest from 0 is positive.

`project` gives each row's score on each of `directions`. The starter's `scale` standardizes measurements by the training beans' statistics. The tests compare your components with those of scikit-learn's `PCA`, which turns them the same way.
