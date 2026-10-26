from dataclasses import dataclass


@dataclass(frozen=True)
class Timing:
    question: str
    release: str
    first: float
    whole: float


def read(path):
    """Each request's timing in the file at path: its seconds to the first piece of the reply,
    the prompt and one token, and to the whole reply."""
    raise NotImplementedError


def percentile(values, share):
    """The smallest of the values that at least share of them are at or below."""
    raise NotImplementedError


def per_hour(seconds):
    """How many replies an hour one server writes, one at a time, at the seconds they take."""
    raise NotImplementedError


def busy(peak, hourly):
    """The share of each hour the server spends replying at peak questions an hour."""
    raise NotImplementedError
