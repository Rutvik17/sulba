# /// script
# requires-python = "==3.14.2"
# dependencies = [
#   "jsonschema==4.26.0",
# ]
# ///
"""Records the errors jsonschema finds in the shop's cases, for the lab's tests.

Each case is a JSON Schema and a value, and jsonschema's Draft202012Validator, with no format
checker, as it validates by default, lists the value's errors. validation.json holds each case
with its errors, each as its JSON path and the keyword it fails, sorted.

    uv run make.py <folder to write in> <folder of the lab's data>
"""

import json
import sys
from importlib.metadata import version
from pathlib import Path

from jsonschema import Draft202012Validator

BOOKING = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 60},
        "bike": {"enum": ["road", "mountain", "city", "cargo", "e-bike"]},
        "service": {"enum": ["puncture", "brakes", "gears", "full service"]},
        "date": {"type": "string", "format": "date"},
        "time": {"type": "string", "pattern": "^(09|1[0-6]):[03]0$"},
        "bikes": {"type": "integer", "minimum": 1, "maximum": 3},
        "phone": {"type": ["string", "null"], "pattern": "^\\+?[0-9 ]{7,15}$"},
        "notes": {"type": "string", "maxLength": 500},
    },
    "required": ["name", "bike", "service", "date", "time", "bikes", "phone", "notes"],
    "additionalProperties": False,
}
REPLY = {
    "name": "Ana Silva",
    "bike": "city",
    "service": "brakes",
    "date": "2026-10-24",
    "time": "10:30",
    "bikes": 1,
    "phone": "+44 7700 900123",
    "notes": "The rear brake squeals.",
}
ORDER = {
    "type": "object",
    "properties": {
        "bikes": {
            "type": "array",
            "minItems": 1,
            "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "kind": {"enum": ["road", "mountain", "city", "cargo", "e-bike"]},
                    "wheel size": {"type": "integer"},
                },
                "required": ["kind"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["bikes"],
    "additionalProperties": False,
}


def reply(**changes):
    """The booking reply with some fields changed, and those given ... removed."""
    changed = {**REPLY, **changes}
    return {key: value for key, value in changed.items() if value is not ...}


# Each group of cases is one test's: (schema, value) pairs.
CASES = {
    "types": [
        ({"type": "integer"}, 3),
        ({"type": "integer"}, 3.0),
        ({"type": "integer"}, 3.5),
        ({"type": "integer"}, True),
        ({"type": "integer"}, "3"),
        ({"type": "number"}, 2.5),
        ({"type": "number"}, False),
        ({"type": "boolean"}, 0),
        ({"type": "null"}, None),
        ({"type": "string"}, None),
        ({"type": ["string", "null"]}, None),
        ({"type": ["string", "null"]}, 5),
        ({"type": "array"}, {}),
        ({"type": "object"}, []),
        ({}, {"anything": [1, "two", None]}),
    ],
    "equality": [
        ({"enum": [1, 2, 3]}, 2),
        ({"enum": [1, 2, 3]}, 1.0),
        ({"enum": [1, 2, 3]}, True),
        ({"enum": [False, None]}, 0),
        ({"enum": [False, None]}, None),
        ({"enum": ["road", "city"]}, "Road"),
        ({"enum": [[1, 2], {"a": 1}]}, [1, 2]),
        ({"enum": [[1, 2], {"a": 1}]}, {"a": True}),
        ({"const": "booking"}, "booking"),
        ({"const": 0}, False),
        ({"const": 0}, 0.0),
    ],
    "objects": [
        (BOOKING, reply()),
        (BOOKING, reply(phone=..., notes=...)),
        (BOOKING, reply(price=0, confirmed=True)),
        (BOOKING, reply(bike="bmx", bikes="2", time="9:30")),
        (BOOKING, reply(bikes=2.0)),
        (BOOKING, reply(bikes=0)),
        (BOOKING, reply(bikes=4, name="")),
        (BOOKING, [REPLY]),
        (
            {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "additionalProperties": {"type": "integer"},
            },
            {"name": "Ana", "age": "40", "size": 54},
        ),
        (
            {"properties": {"name": {"type": "string"}}, "additionalProperties": True},
            {"name": "Ana", "age": "40"},
        ),
        ({"required": ["name"]}, "name"),
    ],
    "arrays": [
        (ORDER, {"bikes": [{"kind": "road"}, {"kind": "city", "wheel size": 28}]}),
        (ORDER, {"bikes": []}),
        (
            ORDER,
            {
                "bikes": [
                    {"kind": "road"},
                    {"kind": "bmx", "wheel size": 20.5},
                    {"colour": "red"},
                    {"kind": "city"},
                ]
            },
        ),
        ({"maxItems": 1}, "not an array"),
    ],
    "strings": [
        ({"type": "string", "minLength": 2}, "🚲"),
        ({"type": "string", "minLength": 2}, "é"),
        ({"type": "string", "minLength": 2}, "é"),
        ({"type": "string", "maxLength": 3}, "four"),
        ({"maxLength": 2}, 12345),
        ({"type": "string", "pattern": "[0-9]{4}"}, "Call 01234 567890"),
        ({"type": "string", "pattern": "[0-9]{4}"}, "Call the shop"),
        (BOOKING, reply(time="10:00\n")),
        (BOOKING, reply(time="10:00 or 14:00")),
        (BOOKING, reply(phone="call me")),
        (BOOKING, reply(phone=None)),
    ],
    "numbers": [
        ({"type": "number", "maximum": 3}, 3),
        ({"type": "number", "maximum": 3}, 3.5),
        ({"minimum": 1}, 0),
        ({"minimum": 1}, "0"),
        ({"minimum": 1}, False),
    ],
    "formats": [
        (BOOKING, reply(date="2026-02-30")),
        (BOOKING, reply(date="next Tuesday")),
    ],
}


def main(folder, data):
    recording = {"jsonschema": version("jsonschema"), "cases": {}}
    for group, cases in CASES.items():
        recording["cases"][group] = [
            {
                "schema": schema,
                "value": value,
                "errors": sorted(
                    [error.json_path, error.validator]
                    for error in Draft202012Validator(schema).iter_errors(value)
                ),
            }
            for schema, value in cases
        ]
    (folder / "validation.json").write_text(
        json.dumps(recording, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
