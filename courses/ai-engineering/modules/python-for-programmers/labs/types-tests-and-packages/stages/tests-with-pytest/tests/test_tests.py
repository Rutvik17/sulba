import sys

import pytest

pytest_plugins = ["pytester"]

# The port as it should be, which every mutant below changes in one place.
PORT = r'''
"""The clinic's checks, with the types mypy holds them to."""

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import NotRequired, TypedDict, TypeGuard


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


class StructError(TypeError):
    """A value that fails a struct, with superstruct's message."""


class Struct[T]:
    """A check of values of one type: its name, and a test that tells values of the type
    apart."""

    def __init__(self, name: str, test: Callable[[object], TypeGuard[T]]) -> None:
        self.name = name
        self.test = test


def is_string(value: object) -> TypeGuard[str]:
    """Whether the value is a string."""
    return isinstance(value, str)


def string() -> Struct[str]:
    """A struct of strings."""
    return Struct("string", is_string)


def is_number(value: object) -> TypeGuard[float]:
    """Whether the value is an int or a float other than NaN, and not a bool."""
    return check_number(value) is None


def number() -> Struct[float]:
    """A struct of numbers."""
    return Struct("number", is_number)


def array[T](item: Struct[T]) -> Struct[list[T]]:
    """A struct of lists whose every item passes item."""

    def test(value: object) -> TypeGuard[list[T]]:
        return isinstance(value, list) and all(item.test(each) for each in value)

    return Struct("array", test)


def nullable[T](struct: Struct[T]) -> Struct[T | None]:
    """The struct, with None let through."""

    def test(value: object) -> TypeGuard[T | None]:
        return value is None or struct.test(value)

    return Struct(struct.name, test)


def is_[T](value: object, struct: Struct[T]) -> TypeGuard[T]:
    """Whether the value passes the struct."""
    return struct.test(value)


def create[T](value: object, struct: Struct[T]) -> T:
    """The value, as the struct's type, or StructError when it fails the struct."""
    if struct.test(value):
        return value
    raise StructError(
        f"Expected a value of type `{struct.name}`, but received: `{value!r}`"
    )
'''


@pytest.fixture
def outcomes(pytester, pytestconfig):
    """How many of the tests in test_typed.py pass and fail against a port."""
    tests = (pytestconfig.rootpath / "test_typed.py").read_text()

    def run(port):
        for name in ["typed", "test_typed"]:
            sys.modules.pop(name, None)
        pytester.makepyfile(typed=port, test_typed=tests)
        passed, _, failed = pytester.inline_run(
            "-p", "no:terminal", "-p", "no:cacheprovider"
        ).countoutcomes()
        return passed, failed

    return run


def mutant(old, new):
    assert PORT.count(old) == 1, old
    return PORT.replace(old, new)


@pytest.mark.id("tst_atglcx")
def test_port(outcomes):
    """Your tests pass on the port"""
    passed, failed = outcomes(PORT)
    assert failed == 0
    assert passed > 0


@pytest.mark.id("tst_zzbiqx")
def test_bools(outcomes):
    """Your tests catch number passing True and False"""
    port = mutant("isinstance(value, bool)", "False")
    assert outcomes(port)[1] > 0


@pytest.mark.id("tst_y1anxn")
def test_nan(outcomes):
    """Your tests catch number passing NaN"""
    port = mutant("or math.isnan(value)", "or False")
    assert outcomes(port)[1] > 0


@pytest.mark.id("tst_vj9bwz")
def test_first_item(outcomes):
    """Your tests catch array checking only its first item"""
    port = mutant("for each in value)", "for each in value[:1])")
    assert outcomes(port)[1] > 0


@pytest.mark.id("tst_smy5je")
def test_tuple(outcomes):
    """Your tests catch array passing a tuple"""
    port = mutant("isinstance(value, list)", "isinstance(value, list | tuple)")
    assert outcomes(port)[1] > 0


@pytest.mark.id("tst_mee74l")
def test_message(outcomes):
    """Your tests catch create's message changing"""
    port = mutant("but received: `{value!r}`", "but received: {value!r}")
    assert outcomes(port)[1] > 0
