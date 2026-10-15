```python
order = np.argsort(column)
values, labels = column[order], said_yes[order]
calls = len(values)
left = np.arange(1, calls)
right = calls - left
yes_left = np.cumsum(labels)[:-1]
yes_right = labels.sum() - yes_left
impurity = (left * gini(yes_left, left) + right * gini(yes_right, right)) / calls
possible = (values[1:] > values[:-1]) & (left >= min_leaf) & (right >= min_leaf)
if not possible.any():
    return None
i = np.flatnonzero(possible)[np.argmin(impurity[possible])]
return (values[i] + values[i + 1]) / 2, impurity[i]
```

The best split of each number column on the training calls, with at least {% $fig.min_leaf %} calls a side, from the least impurity left to the most:

| Column | Threshold | At or below | Above | Impurity |
| --- | --- | --- | --- | --- |
| `pdays` | {% $fig.pdays_t %} | {% $fig.pdays_left %} | {% $fig.pdays_right %} | {% $fig.pdays_g %} |
| `previous` | {% $fig.previous_t %} | {% $fig.previous_left %} | {% $fig.previous_right %} | {% $fig.previous_g %} |
| `age` | {% $fig.age_t %} | {% $fig.age_left %} | {% $fig.age_right %} | {% $fig.age_g %} |
| `campaign` | {% $fig.campaign_t %} | {% $fig.campaign_left %} | {% $fig.campaign_right %} | {% $fig.campaign_g %} |

Each lowers the impurity from the {% $fig.root %} of all the training calls, and `pdays` the most. It holds 999 for a client the bank had never reached, as for {% $fig.never %} of the training calls, and the tree needs no telling: 999 sorts after every real count of days, so the split at {% $fig.pdays_t %} puts the clients reached in an earlier campaign at most {% $fig.pdays_t %} days before on one side, and nearly everyone else on the other.

A split compares a column with a threshold and nothing more, so only the order of a column's values counts. Unlike nearest neighbours, a tree needs no scaling: ages in months, or the logarithm of `campaign`, give the same splits.

After one sort, the cumulative sums score every threshold of a column with a few array operations. Counting each side's calls afresh for every threshold would take a pass over the calls per threshold, a time that grows with the square of the number of calls.
