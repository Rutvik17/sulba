`ColumnTransformer` takes a list of `(name, transformer, columns)`: one entry for the numbers, with `StandardScaler()`, and one for the categories, with `OneHotEncoder(handle_unknown="ignore")`. `make_pipeline(encode, LogisticRegression(max_iter=1000))` puts the classifier after it.

---

`train_test_split(table, test_size=0.3, random_state=SEED, stratify=table["readmitted"])` returns the two parts in order.

---

Fit on `features(learn)` and `learn["readmitted"]`; `predict_proba(features(test))[:, 1]` is the probability of a readmission.
