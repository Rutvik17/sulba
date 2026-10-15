Before the bank uses the forest's list, its managers want to know which details of a client the ranking leans on, measured on calls the forest didn't learn from. Shuffling a column's values among the calls breaks its link with each call's outcome, and how far the AUC falls measures how much the ranking needs it. Write `importances`:

```
importances(score, calls, said_yes, groups, repeats, rng)
    -> {group: (mean fall, standard deviation)}
```

`score` is a function that gives a table of calls their shares of yes, such as `lambda calls: forest_score(trees, encode(calls, categories))`. `groups` names groups of columns, such as `{"age": ["age"], "past contact": ["pdays", "previous", "poutcome"]}`. A group's columns are shuffled together, all in the same order, so that every call keeps its values of the group together.

For each group in turn, and each of `repeats` times, draw an order with `rng.permutation(len(calls))`, give a copy of the calls each of the group's columns in that order, and take the fall: the AUC of the calls' scores less the AUC of the copy's. Return each group's mean fall and the standard deviation of its falls, as `np.mean` and `np.std` give them, and leave the calls as they were.

Hidden tests and checks then measure the forest on the validation calls.
