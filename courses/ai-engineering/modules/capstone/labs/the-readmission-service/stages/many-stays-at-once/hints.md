`stays: list[Stay] = Field(min_length=1, max_length=BATCH_LIMIT)` takes a list of 1 to `BATCH_LIMIT` stays, each read as a `Stay`.

---

`pd.DataFrame([stay.model_dump() for stay in batch.stays])` is a table with a row for each stay, in order. One `predict_proba` on its features scores them all.

---

Move `/predict`'s scoring into a function that takes a list of stays and gives a list of `Prediction`s. `/predict` can then call it with a list of one.
