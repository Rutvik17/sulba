Start `vectors.py`. Standardized, a sample's {% $fig.measurements %} measurements form a vector: an arrow from the records' average, at 0, to the sample. The dot product is how two such vectors are compared: multiply them element by element, and add up the products.

Write `dot`, `norm` and `cosine`: the dot product of two vectors, the length of a vector, which is the square root of its dot product with itself, and the cosine of the angle between two vectors, which is their dot product divided by both their lengths.

Then write `centroids`, the mean of the rows of `Z` in each class: the average benign record, where `y` is 0, then the average malignant record, where `y` is 1.

```
dot(a, b) -> a number
norm(a) -> a number
cosine(a, b) -> a number from -1 to 1
centroids(Z, y) -> (the mean where y is 0, the mean where y is 1)
```

The tests standardize the {% $fig.records %} records with their own mean and standard deviation, and compare your functions with NumPy, SciPy and scikit-learn's `NearestCentroid`.
