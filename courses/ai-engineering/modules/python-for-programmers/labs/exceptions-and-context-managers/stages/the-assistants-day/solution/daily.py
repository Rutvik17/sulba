"""The service's daily run: each export's lines checked, the failed records logged, and a
batch for lines that come one at a time."""

import json
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Failure:
    value: object
    path: tuple
    type: str
    message: str


class Missing:
    def __repr__(self):
        return "undefined"


MISSING = Missing()


class Struct:
    type = "unknown"

    def test(self, value):
        return None

    def entries(self, value):
        return ()

    def failures(self, value, path=()):
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
    def __init__(self, failure, rest):
        if failure.path:
            shown = ".".join(str(key) for key in failure.path)
            super().__init__(f"At path: {shown} -- {failure.message}")
        else:
            super().__init__(failure.message)
        self.path = failure.path
        self.type = failure.type


def assert_(value, struct):
    failures = struct.failures(value)
    first = next(failures, None)
    if first is not None:
        raise StructError(first, failures)


def parse_line(line, number):
    """The record on line number, or a ValueError that names the line."""
    try:
        return json.loads(line)
    except json.JSONDecodeError as error:
        raise ValueError(f"Line {number} isn't JSON") from error


def check_line(line, number, struct):
    """The record on line number, or its StructError with a note that names the line."""
    record = parse_line(line, number)
    try:
        assert_(record, struct)
    except StructError as error:
        error.add_note(f"Line {number}")
        raise
    return record


def check_day(lines, struct):
    """The day's records, or an ExceptionGroup of every line's error, in order."""
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
    """Logs each line whose record fails struct, and lets every other error go on."""
    try:
        check_day(lines, struct)
    except* StructError as group:
        log.extend(f"{error.__notes__[-1]}: {error}" for error in group.exceptions)


class Batch:
    """Lines checked one at a time, their errors raised together when the block ends. A
    struct that raises TypeError of its own is broken, and stops the batch."""

    def __init__(self, struct):
        self.struct = struct
        self.records = []
        self.errors = []

    def check(self, line, number):
        try:
            self.records.append(check_line(line, number, self.struct))
        except (StructError, ValueError) as error:
            self.errors.append(error)
        except TypeError as error:
            raise RuntimeError(f"A struct broke on line {number}") from error

    def __enter__(self):
        return self

    def __exit__(self, kind, error, traceback):
        if error is None and self.errors:
            count = len(self.records) + len(self.errors)
            raise ExceptionGroup(
                f"{len(self.errors)} of {count} lines failed", self.errors
            )
        return False
