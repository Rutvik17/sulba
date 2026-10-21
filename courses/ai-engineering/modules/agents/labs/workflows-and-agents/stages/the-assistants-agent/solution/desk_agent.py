"""The help desk's agent, as an assistant wrote it before you started."""

import time
from typing import Any

import httpx

from agent import SYSTEM, OutOfRounds, Request
from desk import SERVICES, Desk, tools
from workflow import MODEL, SAMPLING

ROUNDS = 8


class DeskAgent:
    """One conversation with the caller, through the desk, from the help pages the chat was
    opened from, or None for the desk's home page."""

    def __init__(self, client: httpx.Client, desk: Desk, page: str | None) -> None:
        self.client = client
        self.desk = desk
        opened = (
            f"The caller opened the chat on the {SERVICES[page]} pages."
            if page
            else "The caller opened the chat on the help desk's home page."
        )
        self.system = {"role": "system", "content": f"{SYSTEM}\n\n{opened}"}
        self.messages: list[dict[str, Any]] = [self.system]
        self.requests: list[Request] = []
        self.turns = 0

    def reply(self, message: str) -> str:
        """The desk's reply to the caller's next message."""
        self.desk.turn = self.turns
        self.turns += 1
        self.messages.append({"role": "user", "content": message})
        messages = self.messages
        for _ in range(ROUNDS):
            body = {
                "model": MODEL,
                "messages": messages,
                "tools": tools(),
                "max_tokens": 768,
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
            self.requests.append(
                Request(
                    usage.get("prompt_tokens", 0),
                    usage.get("completion_tokens", 0),
                    seconds,
                    choice["finish_reason"],
                    tuple(call["function"]["name"] for call in calls),
                )
            )
            kept: dict[str, Any] = {"role": "assistant", "content": said.get("content")}
            if calls:
                kept["tool_calls"] = calls
            messages.append(kept)
            if not calls:
                return said.get("content") or ""
            for call in calls:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": self.run(call),
                    }
                )
        raise OutOfRounds(f"The model still called tools after {ROUNDS} requests.")

    def run(self, call: dict[str, Any]) -> str:
        """The result of a tool the model called, as JSON text."""
        name = call["function"]["name"]
        return self.desk.call(name, call["function"]["arguments"])
