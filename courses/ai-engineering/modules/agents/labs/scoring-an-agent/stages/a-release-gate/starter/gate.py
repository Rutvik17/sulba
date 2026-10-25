"""The desk's release gate: whether a candidate agent may replace the current one, from both
agents' trials of the same tasks."""

from dataclasses import dataclass

from scores import Score


@dataclass(frozen=True)
class Verdict:
    """The candidate's pass^k less the current agent's, over the tasks; the candidate's 90th
    percentile of seconds; and what it was held for, if anything."""

    difference: Score
    tail: Score
    held: tuple[str, ...]

    @property
    def ship(self) -> bool:
        return not self.held


def gate(
    runs: list[dict[str, str]],
    current: str,
    candidate: str,
    *,
    k: int,
    tolerance: float,
    seconds: float,
    confidence: float = 0.95,
) -> Verdict:
    """The verdict on the candidate."""
    raise NotImplementedError
