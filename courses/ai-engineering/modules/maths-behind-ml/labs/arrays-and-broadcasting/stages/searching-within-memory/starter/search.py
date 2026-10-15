# The memory the search may use at once, in bytes.
BUDGET = 32_000_000


class Search:
    """The clinic's search, over records it standardizes once."""

    def __init__(self, records, diagnoses):
        raise NotImplementedError

    def find(self, new, k=5):
        """For each new sample, its k nearest records, nearest first, their distances, and
        the share of them that are malignant, as search gives them, never holding more
        than BUDGET bytes of arrays at once."""
        raise NotImplementedError
