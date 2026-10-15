The distance between two samples `$a$` and `$b$` adds up the squared difference in every measurement:

```math
d(a, b) = \sqrt{\sum_{j=1}^{m} \left(a_j - b_j\right)^2}
```

| Symbol | Meaning |
| --- | --- |
| `$a_j$`, `$b_j$` | Measurement `$j$` of each sample |
| `$m$` | The number of measurements, {% $fig.measurements %} |

Broadcasting compares two shapes from their last axis back. Each pair of lengths must be equal, or one of them 1, and an axis one shape lacks counts as 1. For the {% $fig.new %} new samples against the {% $fig.records %} records:

| Array | Shape |
| --- | --- |
| `A[:, None, :]` | ({% $fig.new %}, 1, {% $fig.measurements %}) |
| `B[None, :, :]` | (1, {% $fig.records %}, {% $fig.measurements %}) |
| Their difference | ({% $fig.new %}, {% $fig.records %}, {% $fig.measurements %}) |
| Its sum over the last axis | ({% $fig.new %}, {% $fig.records %}) |

That gives all {% $fig.pairs %} distances with no Python loop: the looping happens inside NumPy, in compiled code. The cost is the array of differences in between. It holds {% $fig.middle_numbers %} numbers of 8 bytes each, {% $fig.middle_mb %} MB, and it grows with both counts: {% $fig.later_new %} new samples against {% $fig.later_records %} records would need {% $fig.later_mb %} MB.

The chart adds up, for each measurement, its squared differences over every pair of a new sample and a record, as a share of the total. On the raw measurements, the worst area makes up {% $fig.worst_area_share %} and the mean area {% $fig.mean_area_share %}: {% $fig.area_share %} between them, so the nearest records would be little more than the records with the nearest areas. Standardized, every measurement makes up between {% $fig.low_share %}, the {% $fig.low_name %}, and {% $fig.high_share %}, the {% $fig.high_name %}, close to an even {% $fig.even_share %} each.

A column with no spread over the records has nothing to scale. Dividing it by 0 would give `nan` for every sample, and one `nan` among a sample's measurements makes its every distance `nan`. Dividing by 1 instead leaves the column at 0 for every record, so it adds nothing to any distance among them.
