Start `tree.py`. A Portuguese bank phoned its clients to sell them a term deposit, and {% $fig.share %} of the calls made a sale. `data/calls.csv` holds {% $fig.calls %} of its calls, a row each, and in `subscribed`, whether the client said yes. Among the columns that describe a client:

- `age`;
- `campaign`, the calls to the client in this campaign, this one included;
- `pdays`, the days since the bank last reached the client in an earlier campaign, or 999 if it never had;
- `previous`, the calls to the client before this campaign.

Before its next campaign, the bank wants to call the likeliest clients first. A decision tree ranks them by asking questions of each call, such as whether the bank had reached the client before, and giving the share of yes among the training calls that answered the same way. It chooses each question by how well it splits the calls. How mixed a group of calls is, is its Gini impurity: with a share `$p$` of yes,

```math
G = 2p(1 - p)
```

which is 0 when every call said the same and 0.5 for an even mix. The {% $fig.train %} training calls, whose `set` is 0, include {% $fig.yes %} yes, for an impurity of {% $fig.root %}.

A split sends the calls at or below a threshold on one column left, and the rest right. The impurity it leaves is the two sides' impurities, each weighted by its share of the calls:

```math
G_{\text{split}} = \frac{n_L}{n} G_L + \frac{n_R}{n} G_R
```

Write `gini`, and `best_split`, which finds the threshold on a column whose split leaves the least impurity:

```
gini(yes, calls) -> the impurity of calls calls of which yes said yes
best_split(column, said_yes, min_leaf) -> (threshold, impurity), or None
```

`column` is an array of floats and `said_yes` an array of booleans, one for each call. `gini` takes arrays as well as numbers. The rules are those of scikit-learn's `DecisionTreeClassifier`, which the tests compare with:

- A threshold lies halfway between two neighbouring values of the column, so equal values always go the same way.
- Each side keeps at least `min_leaf` calls. When no threshold leaves that many on both sides, return `None`.
- When thresholds tie, the lowest wins.

Sort the column once. Then the yes calls left of every threshold are a cumulative sum, and the impurities of all the thresholds come from array arithmetic, with no loop over them.
