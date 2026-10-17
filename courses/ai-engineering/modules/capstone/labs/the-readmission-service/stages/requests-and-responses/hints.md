`Literal["No", "Ch"]` takes only those values, and `int = Field(ge=0)` only a whole number of 0 or more. `Age` and the code types are literals too.

---

In `predict`, `pd.DataFrame([stay.model_dump()])` is a one-row table of the stay's fields, which `features` turns into the model's inputs.

---

`trained["model"].predict_proba(...)[0, 1]` is the probability. Return `Prediction(probability=..., call=...)`, with `call` set by `trained["threshold"]`.
