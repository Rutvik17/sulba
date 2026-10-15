The plant will rerun the tuning job whenever new records come in, and the pair it ships shouldn't turn on how one shuffle of the folds fell. Repeated cross-validation averages each pair's five-fold RMSE over several shuffles, one for each seed, and chooses by the average.

Ship the job's model as `TunedModel`. It scores every pair with `scores` once for each of `seeds`, averages each pair's RMSE over them, chooses the lowest average with `choose`, and fits the chosen pair on every record with `fitted`.

```
TunedModel(X, y, mixes, seeds=(0, 1)) -> model, tuned on the plant's records
model.scores -> each (degree, penalty)'s average RMSE, in MPa
model.degree, model.penalty -> the pair it chose
model.predict(new) -> one strength per new mix, in MPa
```

`new` has a row of the eight measurements per mix, or is one mix as a single flat row. If you missed any of stage 4's problems, this stage starts from the fixed `tuning.py`. There are no hints. The tests are hidden: you see which pass, but not their inputs. Three more checks decide whether it ships.
