"""Reads a model's reply as it streams in: its text as it comes, and its tool calls once each is
whole."""

import json
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from typing import Any

import httpx

MODEL = "Qwen3.5-0.8B"


class ModelError(Exception):
    """An error the API answered with: its HTTP status and its message."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"{status}: {message}")
        self.status = status
        self.message = message


@dataclass(frozen=True)
class Streamed:
    """A streamed reply, put back together: its text, its tool calls as a whole reply has them,
    why it finished, and the tokens it used."""

    text: str
    tool_calls: list[dict[str, Any]]
    finish_reason: str
    usage: dict[str, int] | None


def stream(
    client: httpx.Client,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    on_text: Callable[[str], None] = lambda piece: None,
) -> Streamed:
    """Asks for a streamed reply to messages, hands each piece of its text to on_text as it
    arrives, and returns the whole reply."""
    body: dict[str, Any] = {
        "model": MODEL,
        "messages": messages,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if tools:
        body["tools"] = tools
    text: list[str] = []
    calls: dict[int, dict[str, Any]] = {}
    finish_reason, usage = "", None
    with client.stream("POST", "/chat/completions", json=body) as response:
        if response.is_error:
            response.read()
            raise ModelError(response.status_code, error_message(response))
        for data in events(lines(response.iter_bytes())):
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            usage = chunk.get("usage") or usage
            for choice in chunk["choices"]:
                delta = choice["delta"]
                if delta.get("content"):
                    text.append(delta["content"])
                    on_text(delta["content"])
                for piece in delta.get("tool_calls") or []:
                    call = calls.setdefault(
                        piece["index"],
                        {
                            "id": "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        },
                    )
                    call["id"] = piece.get("id") or call["id"]
                    function = piece.get("function") or {}
                    call["function"]["name"] += function.get("name") or ""
                    call["function"]["arguments"] += function.get("arguments") or ""
                finish_reason = choice.get("finish_reason") or finish_reason
    return Streamed(
        "".join(text), [calls[i] for i in sorted(calls)], finish_reason, usage
    )


def lines(chunks: Iterable[bytes]) -> Iterator[str]:
    """The stream's lines, each ended by CR LF, LF or CR, as server-sent events end them."""
    rest = b""
    for chunk in chunks:
        rest += chunk
        parts = rest.splitlines(keepends=True)
        # The last part waits for more when it's unfinished, or ends in a CR whose LF may follow.
        rest = parts.pop() if parts and not parts[-1].endswith(b"\n") else b""
        for part in parts:
            yield part.rstrip(b"\r\n").decode()
    if rest:
        yield rest.rstrip(b"\r\n").decode()


def events(text: Iterable[str]) -> Iterator[str]:
    """The data of each server-sent event, its data lines joined by line breaks."""
    data: list[str] = []
    for line in text:
        if not line:
            if data:
                yield "\n".join(data)
            data = []
            continue
        field, _, value = line.partition(":")
        if field == "data":
            data.append(value.removeprefix(" "))


def error_message(response: httpx.Response) -> str:
    """The message of the error in the response's JSON, or the response's text when it has
    none."""
    try:
        return response.json()["error"]["message"]
    except ValueError, KeyError, TypeError:
        return response.text
