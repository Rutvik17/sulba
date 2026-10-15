```python
def __init__(self, train, varieties, k):
    self.mean, self.sd = np.mean(train, axis=0), np.std(train, axis=0)
    self.train = (train - self.mean) / self.sd
    self.varieties, self.k = varieties, k
    nearest_other = []
    for i, bean in enumerate(self.train):
        distances = ((self.train - bean) ** 2).sum(axis=1)
        distances[i] = np.inf
        nearest_other.append(distances.min())
    self.reach = max(nearest_other)
```

The reach is a distance of {% $fig.reach %} in the scaled measurements, and no real bean comes near it: the farthest a validation or test bean is from its nearest training bean is {% $fig.farthest %}. The stones of the checks, Bombay beans grown {% $fig.longer %} times as long, are at least {% $fig.nearest_stone %} from every training bean. The reach is set when the line is, from the training beans alone, so a batch of stones can't stretch it.

Saying UNSURE costs a person's time, and buys accuracy. With {% $fig.k %} neighbours, {% $fig.split %} of the {% $fig.test %} test beans have no variety with more than half the votes, and the line names only {% $fig.split_right %} of them right; it names {% $fig.clear_right %} of the others right, against {% $fig.all_right %} of all the test beans.

The reach only catches what is far from every bean the line knows. Set up without the {% $fig.new %} beans, the line finds {% $fig.new_beyond %} of the {% $fig.new_beans %} {% $fig.new %} test beans out of reach: to the line, they look like varieties it knows. A new variety close to the known ones needs its own training beans, not a distance.
