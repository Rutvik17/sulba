The buyer of the new supplier's harvest wants its make-up: the share of its beans of each variety. The harvest's varieties aren't known, but the groups can name them: group the training beans, name each group by its commonest variety, and give each bean of the harvest the name of its group. A grouping whose names leave out a variety can't count that variety at all, so take the fewest groups, from as many as there are varieties, whose names take in every variety.

Write `named_groups`, `fewest_groups`, `name_beans` and `make_up`, and import `KMeans` from `sklearn.cluster` at the top of `groups.py`:

```
named_groups(train, varieties, k, seed) -> (model, names)
fewest_groups(train, varieties, seed) -> (model, names)
name_beans(model, names, train, batch) -> an array of each bean's name
make_up(model, names, train, harvest) -> {name: share}
```

- `named_groups` fits `KMeans(k, n_init=STARTS, random_state=seed)` to the training beans' scaled measurements, and names each group by the commonest variety among its training beans.
- `fewest_groups` tries k from the number of varieties up, and returns the first named groups whose names take in every variety.
- `name_beans` scales the batch by the training beans' statistics and names each bean by its group, the one whose centre is nearest it.
- `make_up` gives each name's share of the harvest's beans, the names in alphabetical order.

`train`, `batch` and `harvest` hold raw measurements in the columns of `MEASUREMENTS`, and `varieties` each training bean's variety. Hidden tests and checks then estimate the make-up of the validation beans.
