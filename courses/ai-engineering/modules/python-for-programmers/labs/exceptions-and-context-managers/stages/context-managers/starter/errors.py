def noted(note):
    """A context manager that adds note to any error raised in its block, and lets the error
    go on."""
    raise NotImplementedError


class Batch:
    """A context manager for checking lines one at a time: check(line, number) keeps each
    line's record or its error, and the end of the block raises the errors together."""

    def __init__(self, struct):
        self.struct = struct
        self.records = []
        self.errors = []

    def check(self, line, number):
        """Keeps the line's record in records when it passes, or its error in errors."""
        raise NotImplementedError

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, kind, error, traceback):
        raise NotImplementedError
