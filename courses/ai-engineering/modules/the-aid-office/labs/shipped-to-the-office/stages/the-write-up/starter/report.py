from dataclasses import dataclass
from pathlib import Path

from evals import Change

# The questions the office's chat had in its busiest hour last term.
PEAK = 240
CONFIDENCE = 0.95
# The share of replies the times cover.
SLOWEST = 0.95


@dataclass(frozen=True)
class Release:
    name: str
    right: float
    wrong: float
    staff: float
    first: float
    whole: float
    hourly: float
    busy: float


@dataclass(frozen=True)
class Report:
    questions: int
    releases: list[Release]
    wrong: Change
    chosen: str


def to_run(wrong):
    """The release the office should run, given three's share wrong less five's: three, the
    faster, unless its interval lies wholly above 0."""
    raise NotImplementedError


def report(data=Path("data")):
    """The figures the write-up gives, from the recorded replies and their timings."""
    raise NotImplementedError


def markdown(report):
    """The write-up for the office, in Markdown."""
    raise NotImplementedError
