```python
def importances(score, calls, said_yes, groups, repeats, rng):
    base = roc_auc_score(said_yes, score(calls))
    found = {}
    for name, columns in groups.items():
        falls = []
        for _ in range(repeats):
            order = rng.permutation(len(calls))
            shuffled = calls.copy()
            for column in columns:
                shuffled[column] = calls[column].to_numpy()[order]
            falls.append(base - roc_auc_score(said_yes, score(shuffled)))
        found[name] = (float(np.mean(falls)), float(np.std(falls)))
    return found
```

A forest of {% $fig.trees %} trees, measured on the validation calls with {% $fig.repeats %} shuffles of each group:

| Columns shuffled | Mean fall in AUC | Standard deviation |
| --- | --- | --- |
| `contact` | {% $fig.contact_mean %} | {% $fig.contact_spread %} |
| `pdays`, `previous` and `poutcome` together | {% $fig.past_mean %} | {% $fig.past_spread %} |
| `pdays` alone | {% $fig.pdays_mean %} | {% $fig.pdays_spread %} |
| `previous` alone | {% $fig.previous_mean %} | {% $fig.previous_spread %} |
| `poutcome` alone | {% $fig.poutcome_mean %} | {% $fig.poutcome_spread %} |
| `age` | {% $fig.age_mean %} | {% $fig.age_spread %} |
| `day_of_week`, which the forest doesn't read | {% $fig.day_of_week_mean %} | {% $fig.day_of_week_spread %} |

The three columns about the bank's earlier contact with a client carry much the same news. Shuffled one at a time, each loses little, since the forest still finds the news in the other two; shuffled together, they lose more than `age`. Correlated columns share their importance, and each looks smaller alone than what they carry together.

An importance says what the ranking uses, not why clients say yes. `contact` comes first, and the calls are in the order of their dates: telephone calls are {% $fig.early_telephone %} of the first half of the file and {% $fig.late_telephone %} of the second, so `contact` also tells the forest when a call was made.
