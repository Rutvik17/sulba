A seed company's sorting line photographs each bean and measures its shape, from its area in pixels to four shape factors, {% $fig.measurements %} measurements in all. The line names each bean's variety from the beans most like it among those already named: the training beans of `data/beans.csv`, whose `set` is 0.

How alike two beans are is the distance between their measurements. Taken as they are, though, the measurements don't count alike: among the training beans, `Area` has a standard deviation of {% $fig.area_sd %} pixels, and `Solidity` one of {% $fig.solidity_sd %}. Write `scale`, which puts every measurement on one scale: it subtracts the training beans' mean of the measurement and divides by their standard deviation, the one that divides by the number of beans, for the training beans and for any other beans alike.

```
scale(train, other) -> (train_scaled, other_scaled)
```

`train` and `other` are arrays of floats with a row for each bean and a column for each of the starter's `MEASUREMENTS`.
