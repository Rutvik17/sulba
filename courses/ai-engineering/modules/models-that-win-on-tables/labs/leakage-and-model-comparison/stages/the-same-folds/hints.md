Loop over the splits, and inside that over the models. `clone(model).fit(calls.iloc[fit], said_yes[fit])` fits a copy, and its `predict_proba(calls.iloc[held])[:, 1]` gives the held calls' chances of yes.

---

`scores.drop(columns=baseline)` leaves the other models, and `.sub(scores[baseline], axis=0)` takes the baseline's AUC from each row.
