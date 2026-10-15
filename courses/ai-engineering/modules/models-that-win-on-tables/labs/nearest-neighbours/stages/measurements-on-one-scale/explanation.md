```python
mean = np.mean(train, axis=0)
sd = np.std(train, axis=0)
return (train - mean) / sd, (other - mean) / sd
```

Measured as they are, the distance between two beans is the distance between their areas. Between two training beans picked at random, `Area` and `ConvexArea` make up {% $fig.share %} of the squared distance on average, and a bean's shape counts for almost nothing. Named by the varieties of their {% $fig.k %} nearest training beans, the validation beans come out right {% $fig.unscaled %} of the time on the raw measurements, and {% $fig.scaled %} once every measurement is standardized.

The mean and standard deviation come from the training beans alone, and stay fixed for every bean sorted after. A bean scaled by the statistics of the beans it arrives with would move whenever its batch changed, and so would its nearest beans. Standardizing also takes away the units: areas in square millimetres scale to the same numbers as areas in pixels.

NumPy's `std` divides by the number of beans, as scikit-learn's `StandardScaler` does. pandas' `std` divides by one less, so the same column gives slightly different numbers in pandas and in NumPy.
