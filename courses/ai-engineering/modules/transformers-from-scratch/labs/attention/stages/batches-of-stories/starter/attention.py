def pad(stories, side="right"):
    """Stories of different lengths, each (length, width), as one batch
    (batch, longest, width), padded with zeros after each story, or before it if side is
    "left", and booleans (batch, longest), True at each story's own tokens."""
    raise NotImplementedError


def batch_mask(present, causal=True):
    """Booleans (batch, 1, longest, longest), True where a query may see a key: where the key
    is one of its story's own tokens, and, if causal, no later than the query."""
    raise NotImplementedError


def unpad(batch, present):
    """Each story's own rows of batch (batch, longest, width), as a list in order."""
    raise NotImplementedError
