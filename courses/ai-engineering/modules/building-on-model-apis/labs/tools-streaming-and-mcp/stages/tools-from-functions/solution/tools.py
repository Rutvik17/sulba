"""The shop's Python functions as tools a model can call, and the calls it makes to them."""

import inspect
import json
import re
import types
import typing
from collections.abc import Callable
from typing import Annotated, Any, Literal

# A tool's name, as the chat completions API takes it.
NAME = re.compile(r"[a-zA-Z0-9_-]{1,64}")
TYPES = {str: "string", int: "integer", float: "number", bool: "boolean"}


def describe(function: Callable[..., Any]) -> dict[str, Any]:
    """The tool a function is, as the chat completions API takes it: its name, its docstring as
    the description, and a strict schema of its parameters."""
    if not NAME.fullmatch(function.__name__):
        raise ValueError(f"{function.__name__!r} can't be a tool's name")
    hints = typing.get_type_hints(function, include_extras=True)
    properties = {
        name: schema(hints[name]) for name in inspect.signature(function).parameters
    }
    return {
        "type": "function",
        "function": {
            "name": function.__name__,
            "description": inspect.getdoc(function) or "",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": list(properties),
                "additionalProperties": False,
            },
            "strict": True,
        },
    }


def schema(annotation: Any) -> dict[str, Any]:
    """The JSON Schema of a parameter's type."""
    origin, arguments = typing.get_origin(annotation), typing.get_args(annotation)
    if origin is Annotated:
        return {**schema(arguments[0]), "description": arguments[1]}
    if origin is Literal and all(isinstance(each, str) for each in arguments):
        return {"type": "string", "enum": list(arguments)}
    if origin is list:
        return {"type": "array", "items": schema(arguments[0])}
    if origin in (types.UnionType, typing.Union) and type(None) in arguments:
        [inner] = [each for each in arguments if each is not type(None)]
        found = schema(inner)
        if "enum" in found:
            found["enum"] = [*found["enum"], None]
        return {**found, "type": [found["type"], "null"]}
    if annotation in TYPES:
        return {"type": TYPES[annotation]}
    raise TypeError(f"No JSON Schema for {annotation!r}")


def run(
    functions: dict[str, Callable[..., Any]], call: dict[str, Any]
) -> dict[str, str]:
    """The tool message that answers a tool call: what the function returns, as JSON, or why it
    couldn't run, as {"error": ...}."""
    name, text = call["function"]["name"], call["function"]["arguments"]
    try:
        function = functions[name]
    except KeyError:
        return answer(call, {"error": f"There's no tool called {name!r}."})
    try:
        arguments = json.loads(text)
    except json.JSONDecodeError as error:
        return answer(call, {"error": f"The arguments aren't JSON: {error}"})
    expected = set(inspect.signature(function).parameters)
    if not isinstance(arguments, dict) or set(arguments) != expected:
        return answer(call, {"error": f"{name} takes {sorted(expected)}."})
    try:
        result = function(**arguments)
    except Exception as error:
        return answer(call, {"error": str(error)})
    return answer(call, result)


def answer(call: dict[str, Any], result: Any) -> dict[str, str]:
    """The tool message for a call, with result as its JSON."""
    content = json.dumps(result, ensure_ascii=False)
    return {"role": "tool", "tool_call_id": call["id"], "content": content}
