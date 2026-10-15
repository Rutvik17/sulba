The plant will check each new mix with the model before it pours it. Ship the model as `StrengthModel`.

It chooses the degree and penalty with `choose`, fits on the training mixes with `model`, and keeps each measurement's lowest and highest value in the training mixes. `accepts` says whether each mix has every measurement inside those ranges. `predict` gives each mix's strength, but raises a `ValueError` if any mix isn't accepted, since the model was fit only on mixes inside them.

```
StrengthModel(train, validation) -> model, with train and validation as (X, y)
model.degree, model.penalty -> the pair it chose
model.accepts(mixes) -> one True or False per mix
model.predict(mixes) -> one strength per mix, in MPa
```

`mixes` has a row of the eight measurements per mix, or is one mix as a single flat row. If you missed any of stage 4's problems, this stage starts from the fixed `strength.py`. There are no hints. The tests are hidden: you see which pass, but not their inputs. Three more checks decide whether it ships.
