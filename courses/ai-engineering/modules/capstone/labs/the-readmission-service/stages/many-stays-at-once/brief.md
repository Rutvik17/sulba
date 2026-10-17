Each morning the planners' system asks about the day's discharges, often dozens at once. A request for each stay would repeat the request's own work, and the model's, for every one, so the service takes them in batches:

```
POST /predict/batch, with {"stays": [stay, ...]} -> {"predictions": [prediction, ...]}
```

`Batch` holds 1 to `BATCH_LIMIT` stays, each a `Stay`, and `Predictions` holds the answer for each, in the batch's order, each a `Prediction`. FastAPI answers a 422 for a batch with no stays, with more than `BATCH_LIMIT`, or with a stay that doesn't fit, and its `detail` names that stay by its place in the list.

Score the whole batch with one call to the model, on a table of all its stays, and give each stay the answer `/predict` gives it. The tests compare your answers with the saved model's, and with `/predict`'s.
