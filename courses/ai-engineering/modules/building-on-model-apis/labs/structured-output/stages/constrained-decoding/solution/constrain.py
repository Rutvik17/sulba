"""Constrained decoding: a reply written token by token, each token one that can still lead to
a reply the schema allows."""

import json
from collections.abc import Callable
from typing import Any

END = "<|im_end|>"
# Where scan says a value ends when the text stops partway through a value that can still be
# valid: past the end of any text.
MORE = 1 << 30


def allowed(text: str, schema: dict[str, Any]) -> bool:
    """Whether text is the start of a reply the schema allows, or a whole one."""
    return scan(text, 0, schema) in (len(text), MORE)


def complete(text: str, schema: dict[str, Any]) -> bool:
    """Whether text is a whole reply the schema allows."""
    return scan(text, 0, schema) == len(text)


def mask(text: str, vocabulary: list[str], schema: dict[str, Any]) -> list[bool]:
    """For each token of the vocabulary, whether it can come after text: END once text is a
    whole reply, and any other token when text and it are the start of one."""
    return [
        complete(text, schema) if token == END else allowed(text + token, schema)
        for token in vocabulary
    ]


def generate(
    scores: Callable[[str], list[float]],
    vocabulary: list[str],
    schema: dict[str, Any],
    max_tokens: int,
) -> tuple[str, str]:
    """The reply the model writes: at each step, of the tokens that can come next, the one it
    scores highest, the first of them on a tie. Returns the text and "stop" when it chooses END,
    or "length" when it has written max_tokens tokens."""
    text = ""
    for _ in range(max_tokens):
        can, score = mask(text, vocabulary, schema), scores(text)
        best = max((i for i, ok in enumerate(can) if ok), key=lambda i: score[i])
        if vocabulary[best] == END:
            return text, "stop"
        text += vocabulary[best]
    return text, "length"


def scan(text: str, index: int, schema: dict[str, Any]) -> int | None:
    """Where the value schema allows, starting at text[index], ends: MORE when text stops
    partway through one, and None when none starts there."""
    if "enum" in schema:
        options = [json.dumps(each, ensure_ascii=False) for each in schema["enum"]]
        return one_of(text, index, options)
    match schema["type"]:
        case "object":
            return scan_object(text, index, schema)
        case "string":
            return scan_string(text, index, schema)
        case "integer":
            return scan_integer(text, index, schema)
        case "boolean":
            return one_of(text, index, ["true", "false"])
    raise ValueError(f"Unsupported schema {schema!r}")


def literal(text: str, index: int, expected: str) -> int | None:
    """Where expected ends when text has it at index, MORE when text stops partway through it,
    and None when text has something else."""
    rest = text[index:]
    if rest.startswith(expected):
        return index + len(expected)
    return MORE if expected.startswith(rest) else None


def one_of(text: str, index: int, options: list[str]) -> int | None:
    """Like literal, for one of several texts, none of which starts another."""
    ends = [
        end
        for end in (literal(text, index, each) for each in options)
        if end is not None
    ]
    return min(ends, default=None)


def scan_object(text: str, index: int, schema: dict[str, Any]) -> int | None:
    """An object with every property, in the schema's order, and no spaces."""
    end = literal(text, index, "{")
    for number, (key, subschema) in enumerate(schema["properties"].items()):
        if end is None or end == MORE:
            return end
        end = literal(text, end, ("," if number else "") + json.dumps(key) + ":")
        if end is None or end == MORE:
            return end
        end = scan(text, end, subschema)
    if end is None or end == MORE:
        return end
    return literal(text, end, "}")


def scan_string(text: str, index: int, schema: dict[str, Any]) -> int | None:
    """A string of minLength to maxLength characters, with no quote, backslash or control
    character in it."""
    if index == len(text):
        return MORE
    if text[index] != '"':
        return None
    least, most = schema.get("minLength", 0), schema.get("maxLength", MORE)
    for count, character in enumerate(text[index + 1 :]):
        if character == '"':
            return index + count + 2 if count >= least else None
        if character == "\\" or ord(character) < 0x20 or count == most:
            return None
    return MORE


def scan_integer(text: str, index: int, schema: dict[str, Any]) -> int | None:
    """An integer from minimum to maximum, both at least 0, with no leading zero."""
    end = index
    while end < len(text) and text[end] in "0123456789":
        end += 1
    digits = text[index:end]
    if len(digits) > 1 and digits[0] == "0":
        return None
    values = range(schema["minimum"], schema["maximum"] + 1)
    if end == len(text):
        return MORE if any(str(value).startswith(digits) for value in values) else None
    return end if digits and int(digits) in values else None
