"""The shop's Python functions as tools a model can call, and the calls it makes to them."""

from collections.abc import Callable
from typing import Any


def describe(function: Callable[..., Any]) -> dict[str, Any]:
    """The tool a function is, as the chat completions API takes it: its name, its docstring as
    the description, and a strict schema of its parameters."""
    raise NotImplementedError


def run(
    functions: dict[str, Callable[..., Any]], call: dict[str, Any]
) -> dict[str, str]:
    """The tool message that answers a tool call: what the function returns, as JSON, or why it
    couldn't run, as {"error": ...}."""
    raise NotImplementedError
