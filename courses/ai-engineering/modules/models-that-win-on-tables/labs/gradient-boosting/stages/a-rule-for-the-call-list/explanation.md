```python
def frame(calls):
    columns = calls[NUMBERS + CATEGORIES].copy()
    for name in CATEGORIES:
        columns[name] = columns[name].astype("category")
    return columns


def call_model(train, validation, rule):
    rules = {}
    if rule:
        rules["monotone_constraints"] = [
            -1 if name == "campaign" else 0 for name in NUMBERS + CATEGORIES
        ]
    model = LGBMClassifier(
        n_estimators=ROUNDS, learning_rate=RATE, num_leaves=LEAVES, verbose=-1, **rules
    )
    model.fit(
        frame(train),
        (train["subscribed"] == "yes").to_numpy(),
        eval_set=[(frame(validation), (validation["subscribed"] == "yes").to_numpy())],
        callbacks=[early_stopping(PATIENCE, verbose=False)],
    )
    return model


def raised(model, clients, more):
    now = model.predict_proba(frame(clients))[:, 1]
    higher = np.zeros(len(clients), dtype=bool)
    for extra in range(1, more + 1):
        later = clients.copy()
        later["campaign"] = later["campaign"] + extra
        higher |= model.predict_proba(frame(later))[:, 1] > now
    return int(higher.sum())
```

| | Without the rule | With the rule |
| --- | --- | --- |
| Rounds kept | {% $fig.free_kept %} | {% $fig.ruled_kept %} |
| AUC on the validation calls | {% $fig.free_validation %} | {% $fig.ruled_validation %} |
| AUC on the test calls | {% $fig.free_test %} | {% $fig.ruled_test %} |
| Validation clients moved up by up to {% $fig.more %} calls more | {% $fig.free_raised %} | {% $fig.ruled_raised %} |

Without the rule, {% $fig.free_raised %} of the {% $fig.validation %} validation clients would move up the list for being called again, {% $fig.second_up %} of the {% $fig.once %} called once by a second call alone. With it, none would, and the AUC on the test calls goes from {% $fig.free_test %} to {% $fig.ruled_test %}: the rule costs the ranking little.

The first validation client, a {% $fig.client_job %} aged {% $fig.client_age %}, as each model scores them for the calls made:

| Calls made | Without the rule | With the rule |
| --- | --- | --- |
| {% $fig.calls_1 %} | {% $fig.free_1 %} | {% $fig.ruled_1 %} |
| {% $fig.calls_2 %} | {% $fig.free_2 %} | {% $fig.ruled_2 %} |
| {% $fig.calls_3 %} | {% $fig.free_3 %} | {% $fig.ruled_3 %} |
| {% $fig.calls_4 %} | {% $fig.free_4 %} | {% $fig.ruled_4 %} |
| {% $fig.calls_5 %} | {% $fig.free_5 %} | {% $fig.ruled_5 %} |
| {% $fig.calls_6 %} | {% $fig.free_6 %} | {% $fig.ruled_6 %} |

LightGBM codes the categories too: it keeps the training calls' categories with the model and codes the calls it scores by them, with a category they never had as missing. The coding the assistant's ranking got wrong comes with the model.
