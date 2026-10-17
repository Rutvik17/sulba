One call to `predict_proba` on a table of stays scores them together: the pipeline scales, encodes and weighs the whole table at once, in NumPy, so a batch costs little more than a single stay. A loop that scored each stay on its own would pay for the pipeline's work once per stay.

The limit bounds the work of any one request. `predict_batch` is `async def`, so it runs on the service's event loop, and while it scores a batch, no other request on that loop can run. Without a limit, a single request with a million stays could hold the service for as long as they take. With one, a client with more stays sends more batches, and each waits its turn.

A 422 for a batch names the field by its path through the request, with the stay's index in the list, such as `["body", "stays", 3, "time_in_hospital"]`. The planners' system can tell which stay to fix, and the batch's other stays are answered once it sends again.
