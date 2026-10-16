"""superstruct's errors, ported: the error a value that fails raises, and the ways to check
a value with it."""

import json
import math
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass(frozen=True)
class Failure:
    """One failure of a value against a struct: the value, the path to it, the type of the
    struct it failed, superstruct's message, and the refinement it failed, if any."""

    value: object
    path: tuple
    type: str
    message: str
    refinement: str | None = None


class Missing:
    """The value of a field a record leaves out, shown as JavaScript shows undefined."""

    def __repr__(self):
        return "undefined"


MISSING = Missing()


class Struct:
    """A kind of value: its type, a test of a value, and the values inside one that passes."""

    type = "unknown"

    def test(self, value):
        """None when value is of this struct's kind, or superstruct's message."""
        return None

    def entries(self, value):
        """Each value inside value, as (key, value, struct)."""
        return ()

    def failures(self, value, path=()):
        """Each Failure of value against this struct, found as it's asked for."""
        message = self.test(value)
        if message is not None:
            yield Failure(value, path, self.type, message)
            return
        for key, item, struct in self.entries(value):
            yield from struct.failures(item, (*path, key))


class String(Struct):
    type = "string"

    def test(self, value):
        if isinstance(value, str):
            return None
        return f"Expected a string, but received: {value!r}"


class Number(Struct):
    type = "number"

    def test(self, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return f"Expected a number, but received: {value!r}"
        if isinstance(value, float) and math.isnan(value):
            return f"Expected a number, but received: {value!r}"
        return None


class Never(Struct):
    type = "never"

    def test(self, value):
        return f"Expected a value of type `never`, but received: `{value!r}`"


class Object(Struct):
    type = "object"

    def __init__(self, schema):
        self.schema = dict(schema)

    def test(self, value):
        if isinstance(value, dict):
            return None
        return f"Expected an object, but received: {value!r}"

    def entries(self, value):
        for key, struct in self.schema.items():
            yield key, value.get(key, MISSING), struct
        for key in value:
            if key not in self.schema:
                yield key, value[key], Never()


class StructError(TypeError):
    """superstruct's StructError: a TypeError for a value's first failure, which finds the
    rest when they're asked for."""

    def __init__(self, failure, rest):
        if failure.path:
            shown = ".".join(str(key) for key in failure.path)
            message = f"At path: {shown} -- {failure.message}"
        else:
            message = failure.message
        super().__init__(message)
        self.value = failure.value
        self.path = failure.path
        self.key = failure.path[-1] if failure.path else None
        self.type = failure.type
        self.refinement = failure.refinement
        self._first = failure
        self._rest = rest
        self._found = None

    def failures(self):
        """Every failure of the value, the first included, found the first time they're
        asked for."""
        if self._found is None:
            self._found = [self._first, *self._rest]
        return self._found


def assert_(value, struct):
    """None when value passes struct, or raises the StructError of its first failure."""
    failures = struct.failures(value)
    first = next(failures, None)
    if first is not None:
        raise StructError(first, failures)


def validate(value, struct):
    """(None, value) when value passes struct, or (error, None) with its StructError."""
    try:
        assert_(value, struct)
    except StructError as error:
        return error, None
    else:
        return None, value


def is_(value, struct):
    """Whether value passes struct."""
    error, _ = validate(value, struct)
    return error is None


def parse_line(line, number):
    """The record on line number of a day's export, or raises a ValueError that names the
    line, from json's own error."""
    try:
        return json.loads(line)
    except json.JSONDecodeError as error:
        raise ValueError(f"Line {number} isn't JSON") from error


def check_line(line, number, struct):
    """The record on line number when it passes struct, or raises its StructError, with a
    note that names the line."""
    record = parse_line(line, number)
    try:
        assert_(record, struct)
    except StructError as error:
        error.add_note(f"Line {number}")
        raise
    return record


def check_day(lines, struct):
    """The records of a day's lines, numbered from 1, or raises an ExceptionGroup of every
    line's error, in order."""
    records, errors = [], []
    number = 0
    for number, line in enumerate(lines, 1):
        try:
            records.append(check_line(line, number, struct))
        except (StructError, ValueError) as error:
            errors.append(error)
    if errors:
        raise ExceptionGroup(f"{len(errors)} of {number} lines failed", errors)
    return records


def report(lines, struct, log):
    """Adds "Line n: message" to log for each line whose record fails struct. Every other
    error of the day reaches the caller, in a group."""
    try:
        check_day(lines, struct)
    except* StructError as group:
        log.extend(f"{error.__notes__[-1]}: {error}" for error in group.exceptions)


@contextmanager
def noted(note):
    """A context manager that adds note to any error raised in its block, and lets the error
    go on."""
    try:
        yield
    except BaseException as error:
        error.add_note(note)
        raise


class Batch:
    """A context manager for checking lines one at a time: check(line, number) keeps each
    line's record or its error, and the end of the block raises the errors together."""

    def __init__(self, struct):
        self.struct = struct
        self.records = []
        self.errors = []

    def check(self, line, number):
        """Keeps the line's record in records when it passes, or its error in errors."""
        try:
            self.records.append(check_line(line, number, self.struct))
        except (StructError, ValueError) as error:
            self.errors.append(error)

    def __enter__(self):
        return self

    def __exit__(self, kind, error, traceback):
        if error is None and self.errors:
            count = len(self.records) + len(self.errors)
            raise ExceptionGroup(
                f"{len(self.errors)} of {count} lines failed", self.errors
            )
        return False


def check_export(path, struct):
    """The records of the export at path, or raises an ExceptionGroup of every line that
    fails, noted with the export's name."""
    with (
        noted(f"Export {path.name}"),
        open(path, encoding="utf-8") as lines,
        Batch(struct) as batch,
    ):
        for number, line in enumerate(lines, 1):
            batch.check(line, number)
    return batch.records
