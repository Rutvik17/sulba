"""The service's intake: each record checked before it goes on to screening, and the
report's lines for the samples it takes."""

from typing import NotRequired, TypedDict, TypeGuard, cast


class Sample(TypedDict):
    id: str
    radius: float
    note: NotRequired[str]


class IntakeError(TypeError):
    """A record the service can't take, with the field it can't hold."""


def is_radius(value: object) -> TypeGuard[float]:
    """Whether the value is a radius: a number above zero."""
    return isinstance(value, int | float) and not isinstance(value, bool) and value > 0


def take(record: dict[str, object]) -> Sample:
    """The record as a Sample, or IntakeError naming the first field it can't hold."""
    if not isinstance(record.get("id"), str):
        raise IntakeError("id")
    if not is_radius(record.get("radius")):
        raise IntakeError("radius")
    if "note" in record and not isinstance(record["note"], str):
        raise IntakeError("note")
    return cast(Sample, record)


def label(sample: Sample) -> str:
    """The sample's id and radius, for the report."""
    return f"{sample['id']} ({sample['radius']})"


def note_of(sample: Sample) -> str:
    """The sample's note, or an empty string when it has none."""
    return sample.get("note", "")
