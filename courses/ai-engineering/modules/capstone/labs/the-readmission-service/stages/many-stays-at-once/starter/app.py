# The most stays a request can bring at once.
BATCH_LIMIT = 100


class Batch(BaseModel):
    """The stays a batch request asks about, 1 to BATCH_LIMIT of them."""


class Predictions(BaseModel):
    """The service's answer for each stay of a batch, in the batch's order."""
