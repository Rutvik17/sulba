"""The clinic's checks, with the types mypy holds them to."""

import math
from dataclasses import dataclass
from typing import NotRequired, TypedDict


@dataclass(frozen=True)
class Failure:
    """One failure of a value: the keys and indexes that lead to it, and superstruct's
    message."""

    path: tuple[str | int, ...]
    message: str


def explain(failure: Failure) -> str:
    """superstruct's message for the failure, with its path."""
    if not failure.path:
        return failure.message
    shown = ".".join(str(key) for key in failure.path)
    return f"At path: {shown} -- {failure.message}"


def check_number(value: object) -> str | None:
    """None for a number, or superstruct's message."""
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or math.isnan(value)
    ):
        return f"Expected a number, but received: {value!r}"
    return None


class Sample(TypedDict):
    """A sample's record: its id and radius, and a note it may leave out."""

    id: str
    radius: float
    note: NotRequired[str]


def label(sample: Sample) -> str:
    """The sample's id and radius, and its note when it has one."""
    shown = f"{sample['id']} ({sample['radius']})"
    note = sample.get("note")
    return shown if note is None else f"{shown}: {note}"


def failures(record: dict[str, object]) -> list[Failure]:
    """Each field of the record that a Sample can't hold, with its message."""
    found = []
    if not isinstance(record.get("id"), str):
        found.append(
            Failure(("id",), f"Expected a string, but received: {record.get('id')!r}")
        )
    message = check_number(record.get("radius"))
    if message is not None:
        found.append(Failure(("radius",), message))
    if "note" in record and not isinstance(record["note"], str):
        found.append(
            Failure(("note",), f"Expected a string, but received: {record['note']!r}")
        )
    return found
