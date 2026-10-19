"""Checks a JSON value against a JSON Schema: the keywords the shop's assistant uses, as JSON
Schema 2020-12 defines them."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Error:
    """Where a value fails its schema: its JSON path, such as `$.bikes`, the keyword it fails,
    and what's wrong, for a person or a model to read."""

    path: str
    keyword: str
    message: str


def errors(value: Any, schema: dict[str, Any], path: str = "$") -> list[Error]:
    """Every way value fails schema, value being at path in the reply."""
    raise NotImplementedError
