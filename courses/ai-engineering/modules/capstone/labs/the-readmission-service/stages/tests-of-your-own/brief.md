So far the service has been held to the lab's tests. A service you run needs tests of your own, run on every change, to catch a bug before the planners meet it. Write them in `test_app.py`: pytest tests that send requests to the service in process, as the starter's `send` does, with the `loop` fixture.

Your tests must pass on your service, and catch each of these problems, planted one at a time in it:

- It calls at a probability of 0.5, rather than at the saved threshold.
- It answers for a stay of more than 14 days.
- It answers a batch out of order.
- It refuses a full batch of `BATCH_LIMIT` stays.
- It answers for a death or hospice care.

A problem is caught when at least one of your tests fails with it planted. Before your tests run, a model is saved at `MODEL_PATH`, so `load()` gives them the model and threshold the service answers with. Each run here runs your tests six times, once as they are and once for each problem, so keep them to the requests they need.
