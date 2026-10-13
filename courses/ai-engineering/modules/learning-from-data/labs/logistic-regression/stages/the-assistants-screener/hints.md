The assistant's tests check the model on its own and score the whole test set at once. Ask how the clinic will really call `score`: one sample at a time, with its own array, sometimes with a measurement missing.

---

Read each argument the assistant chose on purpose, `copy`, `strategy` and `class_weight`, and each method `score` calls. What does each one do to the clinic's data, or to the model?

---

`predict_proba` returns one column per class, in the order of `model.classes_`. Which column is malignant?
