from jsonschema import Draft202012Validator

BOOKING = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "repair": {"enum": ["tune-up", "brakes", "puncture"]},
        "bikes": {"type": "integer", "minimum": 1, "maximum": 3},
    },
    "required": ["name", "repair", "bikes"],
    "additionalProperties": False,
}


def problems(booking: object) -> list[str]:
    """What is wrong with a booking, each at its place, in order."""
    errors = Draft202012Validator(BOOKING).iter_errors(booking)
    return sorted(f"/{'/'.join(map(str, error.absolute_path))}: {error.message}" for error in errors)
