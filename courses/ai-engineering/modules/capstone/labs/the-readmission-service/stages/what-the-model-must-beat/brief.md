A model's score means little on its own. The planners could already rank patients without one: by how often each was in hospital in the year before. Start `model.py` with the model, a fair test of it, and that ranking to beat.

Write:

```
make_model() -> a new, unfitted scikit-learn pipeline: the counts and age scaled, the categories
    one-hot encoded, ignoring a value it hasn't seen, and a logistic regression
held_out(table) -> (learn, test): the stays split at random, with SEED, into a part to learn
    from and 30% held out, each with the same share readmitted
scores(model, learn, test) -> the model fitted to learn's inputs and readmitted, and its
    probability of a readmission for each stay in test
auc(test, probabilities) -> the area under the ROC curve of those probabilities for test's stays
baseline(test) -> the AUC of ranking test's stays by number_inpatient alone
```

The model takes the inputs `features` makes, so the pipeline's columns are `COUNTS` and `age` to scale, and `CATEGORIES` to encode. Give the logistic regression `max_iter=1000`.

The tests split the {% $fig.learn %} + {% $fig.test %} stays as `train_test_split` does with `test_size=0.3`, `random_state=SEED` and `stratify` set to `readmitted`, and compare your model's probabilities with scikit-learn's own pipeline.
