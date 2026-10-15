The dot product adds up the products of matching elements, and it equals the product of the two lengths and the cosine of the angle between the vectors:

```math
a \cdot b = \sum_{j=1}^{m} a_j b_j = \lVert a \rVert \, \lVert b \rVert \cos\theta
```

| Symbol | Meaning |
| --- | --- |
| `$a_j$`, `$b_j$` | Element `$j$` of each vector |
| `$\lVert a \rVert$` | The length of `$a$`, the square root of `$a \cdot a$` |
| `$\theta$` | The angle between `$a$` and `$b$` |
| `$m$` | The number of measurements, {% $fig.measurements %} |

So the cosine is the dot product of the two vectors once each is scaled to a length of 1: 1 when they point the same way, 0 at a right angle, and -1 when they point opposite ways. It leaves length out, so two samples can have a cosine of 1 and still be far apart.

The average malignant record has a length of {% $fig.length1 %} and the average benign record {% $fig.length0 %}, and the cosine between them is {% $fig.cosine %}: they point in opposite directions. That follows from standardizing. Over all the records, every measurement averages 0, so the {% $fig.malignant %} malignant records and the {% $fig.benign %} benign ones balance:

```math
n_1 \mu_1 + n_0 \mu_0 = 0
```

| Symbol | Meaning |
| --- | --- |
| `$\mu_1$`, `$\mu_0$` | The average malignant and the average benign record |
| `$n_1$`, `$n_0$` | The number of each, {% $fig.malignant %} and {% $fig.benign %} |

Each mean is the other scaled by a negative number, and their lengths stand in the ratio of the counts: {% $fig.length0 %} to {% $fig.length1 %} is {% $fig.ratio %}, as {% $fig.malignant %} to {% $fig.benign %} is {% $fig.count_ratio %}.

The chart shows the two means, measurement by measurement. They are furthest apart in the {% $fig.gap1_name %}, {% $fig.gap1 %} standard deviations, the {% $fig.gap2_name %}, {% $fig.gap2 %}, and the {% $fig.gap3_name %}, {% $fig.gap3 %}, and closest in the {% $fig.least_name %}, {% $fig.least %}.
