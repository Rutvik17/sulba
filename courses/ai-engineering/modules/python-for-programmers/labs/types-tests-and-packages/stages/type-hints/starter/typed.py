"""The clinic's checks, with the types mypy holds them to."""

import math
from dataclasses import dataclass
from typing import NotRequired, TypedDict


@dataclass(frozen=True)
class Failure:
    """One failure of a value: the keys and indexes that lead to it, and superstruct's
    message."""


def explain(failure):
    """superstruct's message for the failure, with its path."""
    raise NotImplementedError


def check_number(value):
    """None for a number, or superstruct's message."""
    raise NotImplementedError


class Sample(TypedDict):
    """A sample's record: its id and radius, and a note it may leave out."""


def label(sample):
    """The sample's id and radius, and its note when it has one."""
    raise NotImplementedError


def failures(record):
    """Each field of the record that a Sample can't hold, with its message."""
    raise NotImplementedError
