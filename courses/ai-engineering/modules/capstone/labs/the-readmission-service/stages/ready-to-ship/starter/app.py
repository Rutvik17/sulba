class Model(BaseModel):
    """The model answering: its threshold, the recall and precision expected there, and the
    versions it was trained with."""


class Stats(BaseModel):
    """How many stays the service has answered since it started, and how many it called."""
