Each round is fitted to the training calls, so their log loss goes down as the rounds go on. The validation calls' log loss goes down too, then turns up once the trees start fitting what is peculiar to the training calls. Two settings decide where that happens: the learning rate, and the number of rounds.

scikit-learn's `GradientBoostingClassifier` boosts as your `boost` does, compiled, and its `staged_predict_proba` gives the rows' shares of yes after each round. Write `losses` and `stop_early`:

```
losses(model, X, said_yes) -> the log loss on the rows after each round
stop_early(history, patience) -> the number of rounds to keep
```

`losses` takes a fitted `GradientBoostingClassifier` and gives the rows' log loss after each of its rounds, as `log_loss` from `sklearn.metrics` computes it from their shares of yes. Import `log_loss` at the top of `boost.py`.

`stop_early` reads a history of validation losses, one for each round, as early stopping does: it goes through the rounds in turn and stops once `patience` rounds in a row have passed without a loss lower than the least so far. It returns the number of rounds up to and including that least loss. A loss equal to the least isn't lower. The tests compare it with the rounds XGBoost keeps when it stops early.

The chart grows a model of 200 rounds of depth 3 with the learning rate the slider sets, and draws your losses on the training and validation calls, with the rounds your `stop_early` keeps at a patience of 20.
