For the threshold, find a stay whose probability is at or above the saved threshold and under 0.5: `load()["model"].predict_proba(features(rows))` scores rows of the extract. The service must call it.

---

For a batch's order, send stays with different probabilities and compare each answer with the saved model's probability for that stay.

---

The refusals each need one request: a stay of 15 days and a death's discharge code each get a 422, and a batch of exactly `BATCH_LIMIT` stays gets a 200.
