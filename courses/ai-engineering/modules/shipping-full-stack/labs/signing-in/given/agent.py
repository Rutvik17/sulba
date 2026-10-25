"""The help desk's agent, as the Tools and planning lab built it, streaming: it reads the
model's reply as it comes and gives each piece of its text, each tool it runs and its reply as
events, for an app to send on. A yes to a proposal makes it in code, before the model reads the
caller's message."""

import json
from collections.abc import AsyncIterable, AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx

from desk import SERVICES, Actions, tools

MODEL = "Qwen3.5-4B"
# The sampling settings Qwen3.5-4B's model card gives for its non-thinking mode.
SAMPLING = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "min_p": 0.0,
    "presence_penalty": 1.5,
}
SYSTEM = (
    "You are the assistant of a help desk for four US public services: Social Security (ssa), "
    "veterans' benefits (va), federal student aid (studentaid) and New York State's DMV (dmv). "
    "The caller is signed in, and the tools act on their account. Today is Friday 30 October "
    "2026. Advisers call back on Monday 2026-11-02, Tuesday 2026-11-03, Wednesday 2026-11-04, "
    "Thursday 2026-11-05 and Friday 2026-11-06, on the hour from 09:00 to 16:00; morning is "
    "before 12:00.\n\n"
    "- Answer questions about the services from their help pages: search them, and cite each "
    "passage you use by its id in square brackets, like [p17]. If the pages don't answer, say "
    "so.\n"
    "- A question about the caller's own case needs an adviser: propose a ticket for its "
    "service.\n"
    "- To arrange a call from an adviser, propose a callback.\n"
    "- A proposal waits for the caller: tell them what it will do and ask them to confirm. The "
    "desk does it when they say yes, and tells you what it did.\n"
    "- If you can't tell what the caller wants, ask them."
)


@dataclass(frozen=True)
class Text:
    """A piece of the reply's text, as it comes."""

    delta: str


@dataclass(frozen=True)
class Tool:
    """A tool the agent runs, by its name, before it runs."""

    name: str


@dataclass(frozen=True)
class Done:
    """The reply as a whole, once it's done, with the tokens of prompt and of reply its
    requests used."""

    text: str
    prompt_tokens: int
    completion_tokens: int


Event = Text | Tool | Done


class ModelError(Exception):
    """An error the model's server answered with: its status and its message."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"{status}: {message}")
        self.status = status
        self.message = message


class OutOfRounds(Exception):
    """The model still called tools after the requests a turn may take."""


class Agent:
    """One conversation with the caller, through the desk's actions, from the help pages the
    chat was opened from, or None for the desk's home page. A turn takes at most rounds
    requests, and prompt_tokens and completion_tokens count what the turn has used so far."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        actions: Actions,
        page: str | None,
        rounds: int = 8,
        max_tokens: int = 768,
    ) -> None:
        self.client = client
        self.actions = actions
        self.rounds = rounds
        self.max_tokens = max_tokens
        opened = (
            f"The caller opened the chat on the {SERVICES[page]} pages."
            if page
            else "The caller opened the chat on the help desk's home page."
        )
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": f"{SYSTEM}\n\n{opened}"}
        ]
        self.turns = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

    async def reply(self, message: str) -> AsyncIterator[Event]:
        """The desk's reply to the caller's next message, as events: each piece of its text as
        it comes, each tool before it runs, then the reply as a whole. A yes makes the proposal
        waiting for it before the model reads the message, which then carries what the desk
        did."""
        self.actions.desk.turn = self.turns
        self.turns += 1
        done = self.actions.heard(message)
        content = message if done is None else f"{message}\n\n(The desk: {done})"
        self.messages.append({"role": "user", "content": content})
        self.prompt_tokens = self.completion_tokens = 0
        for _ in range(self.rounds):
            body = {
                "model": MODEL,
                "messages": self.messages,
                "tools": tools(),
                "max_tokens": self.max_tokens,
                "stream": True,
                "stream_options": {"include_usage": True},
                **SAMPLING,
            }
            text: list[str] = []
            calls: dict[int, dict[str, Any]] = {}
            async with self.client.stream(
                "POST", "/chat/completions", json=body
            ) as response:
                if response.is_error:
                    await response.aread()
                    raise ModelError(response.status_code, error_message(response))
                async for data in events(lines(response.aiter_bytes())):
                    if data == "[DONE]":
                        break
                    chunk = json.loads(data)
                    usage = chunk.get("usage") or {}
                    self.prompt_tokens += usage.get("prompt_tokens", 0)
                    self.completion_tokens += usage.get("completion_tokens", 0)
                    for choice in chunk["choices"]:
                        delta = choice["delta"]
                        if delta.get("content"):
                            text.append(delta["content"])
                            yield Text(delta["content"])
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
                            call["function"]["arguments"] += (
                                function.get("arguments") or ""
                            )
            said = "".join(text)
            made = [calls[index] for index in sorted(calls)]
            kept: dict[str, Any] = {"role": "assistant", "content": said or None}
            if made:
                kept["tool_calls"] = made
            self.messages.append(kept)
            if not made:
                yield Done(said, self.prompt_tokens, self.completion_tokens)
                return
            for call in made:
                yield Tool(call["function"]["name"])
                result = await self.actions.call(
                    call["function"]["name"], call["function"]["arguments"]
                )
                self.messages.append(
                    {"role": "tool", "tool_call_id": call["id"], "content": result}
                )
        raise OutOfRounds(f"The model still called tools after {self.rounds} requests.")


async def lines(chunks: AsyncIterable[bytes]) -> AsyncIterator[str]:
    """The stream's lines, each ended by CR LF, LF or CR, as server-sent events end them."""
    rest = b""
    async for chunk in chunks:
        rest += chunk
        parts = rest.splitlines(keepends=True)
        # The last part waits for more when it's unfinished, or ends in a CR whose LF may follow.
        rest = parts.pop() if parts and not parts[-1].endswith(b"\n") else b""
        for part in parts:
            yield part.rstrip(b"\r\n").decode()
    if rest:
        yield rest.rstrip(b"\r\n").decode()


async def events(text: AsyncIterable[str]) -> AsyncIterator[str]:
    """The data of each server-sent event, its data lines joined by line breaks."""
    data: list[str] = []
    async for line in text:
        if not line:
            if data:
                yield "\n".join(data)
            data = []
            continue
        field, _, value = line.partition(":")
        if field == "data":
            data.append(value.removeprefix(" "))
    if data:
        yield "\n".join(data)


def error_message(response: httpx.Response) -> str:
    """The message of the error in the response's JSON, or the response's text when it has
    none."""
    try:
        return response.json()["error"]["message"]
    except ValueError, KeyError, TypeError:
        return response.text
