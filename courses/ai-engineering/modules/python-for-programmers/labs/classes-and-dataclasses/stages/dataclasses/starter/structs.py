"""superstruct's structs and their failures, ported from JavaScript to classes."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Failure:
    """One failure of a value against a struct: the path to the value, the type of the
    struct it failed, superstruct's message, and the refinement it failed, if any."""

    @property
    def key(self):
        """The key or index of the value in the one around it, or None at the top."""
        raise NotImplementedError

    def explain(self):
        """superstruct's message for the failure, with its path."""
        raise NotImplementedError
