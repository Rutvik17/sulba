"""A conversation's memory: its context within a budget, the notes the model saves, which stay,
and a summary of the turns it no longer holds; and an agent that talks through it."""

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx

from context import Context

MODEL = "Qwen3.5-4B"
# The sampling settings Qwen3.5-4B's model card gives for its non-thinking mode.
SAMPLING = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "min_p": 0.0,
    "presence_penalty": 1.5,
}
SUMMARISE = (
    "Summarise this conversation between a caller and a help desk's assistant for the assistant "
    "who carries it on, who won't see it: what the caller asked, what the assistant told them, "
    "with the ids of the passages it cited, and what the desk did or still has to do. Write at "
    "most 150 words."
)
# The line the desk's system prompt gains, for note.
REMEMBER = (
    "- When the caller tells you something later turns will need, such as when they can take a "
    "call, save it with note.\n"
)
NOTE = {
    "type": "function",
    "function": {
        "name": "note",
        "description": "Save a fact about the caller that later turns will need, such as when "
        "they can take a call. Notes stay when older turns are summarised.",
        "parameters": {
            "type": "object",
            "properties": {"fact": {"type": "string", "description": "One sentence."}},
            "required": ["fact"],
        },
    },
}


class Memory(Context):
    """A Context that keeps the notes the model saves, and over the budget, once there is no
    tool result left to clear, summarises every turn but the last turns, a turn being a caller's
    message and all that follows it. The notes and the summary go in the system message."""

    def __init__(self, system: str, budget: int, keep: int = 2, turns: int = 2) -> None:
        super().__init__(system, budget, keep)
        self.turns = turns
        self.notes: list[str] = []
        self.summary = ""

    def note(self, fact: str) -> str:
        raise NotImplementedError

    def request(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def compact(self, client: httpx.Client) -> bool:
        """Summarises every turn but the last turns, with the summary before them, in one request
        to the model, and keeps the new summary in their place. Gives whether there were turns
        to summarise."""
        raise NotImplementedError

    def fit(self, client: httpx.Client) -> str | None:
        """Before a request: when the last one was over the budget, clears old tool results, or
        when there are none left to clear, summarises older turns. Gives what it did, "cleared"
        or "summarised", or None."""
        raise NotImplementedError


@dataclass(frozen=True)
class Request:
    """One request the agent sent: its tokens of prompt and of reply, the seconds it took, why
    the reply finished, the tools it called, and what the memory did before it."""

    prompt_tokens: int
    completion_tokens: int
    seconds: float
    finish: str
    calls: tuple[str, ...]
    fitted: str | None


class OutOfRounds(Exception):
    """The model still called tools after the requests a turn may take."""


class Agent:
    """One conversation through a memory, with the tools given and note. call runs any other
    tool the model calls, by its name and its arguments as JSON text. heard, given the caller's
    message, gives what the desk did on it, or None. A turn takes at most rounds requests."""

    def __init__(
        self,
        client: httpx.Client,
        memory: Memory,
        tools: list[dict[str, Any]],
        call: Callable[[str, str], str],
        heard: Callable[[str], str | None] | None = None,
        rounds: int = 8,
        max_tokens: int = 768,
    ) -> None:
        self.client = client
        self.memory = memory
        self.tools = [*tools, NOTE]
        self.call = call
        self.heard = heard
        self.rounds = rounds
        self.max_tokens = max_tokens
        self.requests: list[Request] = []

    def run(self, name: str, arguments: str) -> str:
        if name != "note":
            return self.call(name, arguments)
        try:
            given = json.loads(arguments or "{}")
        except json.JSONDecodeError:
            given = None
        if not isinstance(given, dict) or not isinstance(given.get("fact"), str):
            return 'Error: note takes one fact, like {"fact": "They can take calls in the morning."}'
        return self.memory.note(given["fact"])

    def reply(self, message: str) -> str:
        done = self.heard(message) if self.heard else None
        content = message if done is None else f"{message}\n\n(The desk: {done})"
        self.memory.add({"role": "user", "content": content})
        for _ in range(self.rounds):
            fitted = self.memory.fit(self.client)
            body = {
                "model": MODEL,
                "messages": self.memory.request(),
                "tools": self.tools,
                "max_tokens": self.max_tokens,
                **SAMPLING,
            }
            began = time.perf_counter()
            response = self.client.post("/chat/completions", json=body)
            seconds = time.perf_counter() - began
            response.raise_for_status()
            answer = response.json()
            choice = answer["choices"][0]
            said, calls = choice["message"], choice["message"].get("tool_calls") or []
            usage = answer.get("usage") or {}
            self.memory.count(usage)
            self.requests.append(
                Request(
                    usage.get("prompt_tokens", 0),
                    usage.get("completion_tokens", 0),
                    seconds,
                    choice["finish_reason"],
                    tuple(call["function"]["name"] for call in calls),
                    fitted,
                )
            )
            kept: dict[str, Any] = {"role": "assistant", "content": said.get("content")}
            if calls:
                kept["tool_calls"] = calls
            self.memory.add(kept)
            if not calls:
                return said.get("content") or ""
            for call in calls:
                result = self.run(
                    call["function"]["name"], call["function"]["arguments"]
                )
                self.memory.add(
                    {"role": "tool", "tool_call_id": call["id"], "content": result}
                )
        raise OutOfRounds(f"The model still called tools after {self.rounds} requests.")
