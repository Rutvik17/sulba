```python
def components(Z):
    variances, vectors = np.linalg.eigh(np.cov(Z, rowvar=False))
    variances, directions = variances[::-1], vectors[:, ::-1].T
    rows = np.arange(len(directions))
    signs = np.sign(directions[rows, np.abs(directions).argmax(axis=1)])
    return variances, directions * signs[:, np.newaxis]


def project(Z, directions):
    return Z @ directions.T
```

For a direction `$d$` of length 1, the variance of the scores is `$d^\top C d$`, where `$C$` is the covariance matrix. Its largest value is the largest eigenvalue, at that eigenvalue's eigenvector, and among the directions at right angles to it, the next eigenvalue is the largest, and so on down.

Among the {% $fig.train %} training beans, scaled, the first component carries {% $fig.first %} of the variance and the second {% $fig.second %}: two numbers say {% $fig.both %} of what {% $fig.measurements %} say. Keeping {% $fig.kept %} of it takes {% $fig.count %} components, which carry {% $fig.count_share %}.

| Component | Its three largest weights |
| --- | --- |
| First | {% $fig.name_0_0 %} {% $fig.weight_0_0 %}, {% $fig.name_0_1 %} {% $fig.weight_0_1 %}, {% $fig.name_0_2 %} {% $fig.weight_0_2 %} |
| Second | {% $fig.name_1_0 %} {% $fig.weight_1_0 %}, {% $fig.name_1_1 %} {% $fig.weight_1_1 %}, {% $fig.name_1_2 %} {% $fig.weight_1_2 %} |

The scores on the first component follow a bean's length: their correlation with `MajorAxisLength` is {% $fig.length %}. Those on the second rise with its width and fall as it gets longer for its width: their correlations are {% $fig.width %} with `MinorAxisLength` and {% $fig.ratio %} with `AspectRatio`, the major axis over the minor.

Unscaled, each measurement counts by its spread, pixels and ratios alike. The first component of the raw measurements carries {% $fig.raw_first %} of their variance, and its largest weight, {% $fig.raw_weight %}, is on {% $fig.raw_name %}. Scaled, every measurement starts with the same spread, and the components show how the measurements move together.
