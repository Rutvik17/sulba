```python
def named_groups(train, varieties, k, seed):
    Z, _ = scale(train, train)
    model = KMeans(k, n_init=STARTS, random_state=seed).fit(Z)
    names = []
    for group in range(k):
        found, counts = np.unique(varieties[model.labels_ == group], return_counts=True)
        names.append(str(found[counts.argmax()]))
    return model, names


def fewest_groups(train, varieties, seed):
    k = len(set(varieties))
    while True:
        model, names = named_groups(train, varieties, k, seed)
        if set(names) == set(varieties):
            return model, names
        k += 1


def name_beans(model, names, train, batch):
    _, scaled = scale(train, batch)
    return np.array(names)[model.predict(scaled)]


def make_up(model, names, train, harvest):
    named = name_beans(model, names, train, harvest)
    return {name: float(np.mean(named == name)) for name in sorted(set(names))}
```

With {% $fig.varieties %} groups, one for each variety, no group is mostly {% $fig.missing %}, nor with one group more: {% $fig.fewest %} groups are the fewest whose names take in every variety. They name {% $fig.right %} of the {% $fig.harvest %} validation beans right.

| Variety | Share of the harvest | Make-up from the groups |
| --- | --- | --- |
| {% $fig.kind_0 %} | {% $fig.share_0 %} | {% $fig.estimate_0 %} |
| {% $fig.kind_1 %} | {% $fig.share_1 %} | {% $fig.estimate_1 %} |
| {% $fig.kind_2 %} | {% $fig.share_2 %} | {% $fig.estimate_2 %} |
| {% $fig.kind_3 %} | {% $fig.share_3 %} | {% $fig.estimate_3 %} |
| {% $fig.kind_4 %} | {% $fig.share_4 %} | {% $fig.estimate_4 %} |
| {% $fig.kind_5 %} | {% $fig.share_5 %} | {% $fig.estimate_5 %} |
| {% $fig.kind_6 %} | {% $fig.share_6 %} | {% $fig.estimate_6 %} |

{% $fig.wrong %} of the beans are named wrong, yet no variety's share is off by more than {% $fig.worst %}. A variety's share counts the beans named it, so beans of one variety named another are partly balanced by beans of the other named the first. The names are guesses one bean at a time; the make-up is what they add up to.
