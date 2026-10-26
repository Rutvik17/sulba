"""The desk's agent on each kind of contact: the share of each task's trials it did, averaged
over the kind's tasks, with the standard error of that average."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Share:
    """A kind's share of trials done: the mean over its tasks of each task's share, the
    standard error of that mean, and how many tasks it has."""

    value: float
    error: float
    tasks: int


def by_kind(runs: list[dict[str, str]], variant: str) -> dict[str, Share]:
    """Each kind's share for the variant, from runs.csv's rows, in the order the kinds first
    appear."""
    raise NotImplementedError
