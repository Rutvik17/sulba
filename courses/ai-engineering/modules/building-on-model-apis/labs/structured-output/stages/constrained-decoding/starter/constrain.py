"""Constrained decoding: a reply written token by token, each token one that can still lead to
a reply the schema allows."""

from collections.abc import Callable
from typing import Any

END = "<|im_end|>"


def allowed(text: str, schema: dict[str, Any]) -> bool:
    """Whether text is the start of a reply the schema allows, or a whole one."""
    raise NotImplementedError


def complete(text: str, schema: dict[str, Any]) -> bool:
    """Whether text is a whole reply the schema allows."""
    raise NotImplementedError


def mask(text: str, vocabulary: list[str], schema: dict[str, Any]) -> list[bool]:
    """For each token of the vocabulary, whether it can come after text: END once text is a
    whole reply, and any other token when text and it are the start of one."""
    raise NotImplementedError


def generate(
    scores: Callable[[str], list[float]],
    vocabulary: list[str],
    schema: dict[str, Any],
    max_tokens: int,
) -> tuple[str, str]:
    """The reply the model writes: at each step, of the tokens that can come next, the one it
    scores highest, the first of them on a tie. Returns the text and "stop" when it chooses END,
    or "length" when it has written max_tokens tokens."""
    raise NotImplementedError
