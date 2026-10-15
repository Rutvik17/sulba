The score is the nearest-centroid rule in another form. Expanding the two squared distances, the terms in `$\lVert z \rVert^2$` cancel, and what is left is a dot product:

```math
\lVert z - \mu_0 \rVert^2 - \lVert z - \mu_1 \rVert^2 = 2 \left(z - \frac{\mu_0 + \mu_1}{2}\right) \cdot (\mu_1 - \mu_0)
```

| Symbol | Meaning |
| --- | --- |
| `$z$` | A sample, standardized |
| `$\mu_0$`, `$\mu_1$` | The average benign and the average malignant record |

So a sample is nearer the malignant mean exactly when its score is above 0. The samples that score exactly 0 form a flat boundary, a hyperplane, halfway between the two means and at a right angle to the line joining them.

`Z @ u` is a matrix times a vector. With `Z` of shape ({% $fig.new %}, {% $fig.measurements %}) and `u` of {% $fig.measurements %} numbers, it gives {% $fig.new %} scores, each one row's dot product with `u`. The two means are {% $fig.apart %} standard deviations apart, and `u` weights each measurement by how far apart the means are in it: the {% $fig.heaviest_name %} by {% $fig.heaviest %}, the most, and the {% $fig.lightest_name %} by {% $fig.lightest %}.

Of the {% $fig.new %} new samples, {% $fig.malignant_right %} of the {% $fig.malignant %} malignant ones score above 0 and {% $fig.benign_right %} of the {% $fig.benign %} benign ones below it: {% $fig.right %} in all, {% $fig.right_share %}. Moving the threshold trades one kind of mistake for the other, as the chart shows. The rule uses only the two means, and leaves out how the samples spread around each of them.
