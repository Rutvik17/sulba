class Nearest:
    """Finds each new sample's nearest records, from the dot products."""

    def __init__(self, records):
        raise NotImplementedError

    def find(self, new, k=5):
        """Each new sample's k nearest records, nearest first, and their distances, right
        however far the measurements sit from 0."""
        raise NotImplementedError
