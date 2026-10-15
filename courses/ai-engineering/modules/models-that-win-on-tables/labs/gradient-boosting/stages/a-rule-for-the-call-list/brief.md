The call centre has a rule for the list: calling a client again never moves them up it. The calls don't promise that: among the training calls, {% $fig.yes_1 %} of the clients called once subscribed, {% $fig.yes_2 %} of those called twice and {% $fig.yes_3 %} of those called three times, and a model learns from ups and downs like these. LightGBM can hold a model to the rule. Write `frame`, `call_model` and `raised`, and import `LGBMClassifier` and `early_stopping` from `lightgbm` at the top of `boost.py`:

```
frame(calls) -> a DataFrame of the columns the model reads
call_model(train, validation, rule) -> a fitted LGBMClassifier
raised(model, clients, more) -> how many clients more calls would move up
```

`frame` gives the `NUMBERS` columns as they are, then the `CATEGORIES` columns as pandas categories, which LightGBM reads as categories.

`call_model` fits `LGBMClassifier(n_estimators=ROUNDS, learning_rate=RATE, num_leaves=LEAVES, verbose=-1)` to the training calls' frame and whether each said yes. It watches the validation calls with `eval_set` and stops with the callback `early_stopping(PATIENCE, verbose=False)`. With `rule` true, the model also gets `monotone_constraints`, a list with an entry for each column of the frame: `-1` for `campaign`, so that a chance never rises as `campaign` does, and `0` for the others.

`raised` counts the clients whose chance would be higher with any number of calls more, up to `more`, than with `campaign` as it is. Leave the clients as they were.

Hidden tests and checks then train both models on the bank's calls.
