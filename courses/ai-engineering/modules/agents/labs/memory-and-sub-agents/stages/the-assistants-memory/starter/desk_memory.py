"""The assistant's memory for the desk's agent: the conversation within a budget of tokens, the
notes the model saves, and a summary of the turns it no longer holds."""

from typing import Any

import httpx

MODEL = "Qwen3.5-4B"
CLEARED = "Cleared to keep the conversation short. Call {name} again to see it."
SUMMARISE = (
    "Summarise this conversation between a caller and a help desk's assistant for the assistant "
    "who carries it on, who won't see it: what the caller asked, what the assistant told them, "
    "with the ids of the passages it cited, and what the desk did or still has to do. Write at "
    "most 150 words."
)


class DeskMemory:
    """The desk's conversation after its system message, and the tokens its last request took.
    Over the budget, it clears all but the keep most recent tool results, and then summarises
    all but the last turns. The notes the model saves stay in the system message."""

    def __init__(self, system: str, budget: int, keep: int = 2, turns: int = 2) -> None:
        self.system = system
        self.budget = budget
        self.keep = keep
        self.turns = turns
        self.messages: list[dict[str, Any]] = []
        self.notes: list[str] = []
        self.summary = ""
        self.used = 0

    def add(self, message: dict[str, Any]) -> None:
        self.messages.append(message)

    def count(self, usage: dict[str, int]) -> None:
        self.used = usage.get("prompt_tokens", 0)

    def note(self, fact: str) -> str:
        self.notes.append(fact.strip())
        return "Noted."

    def request(self) -> list[dict[str, Any]]:
        system = self.system
        if self.summary:
            system += f"\n\nThe conversation before the messages below, summarised:\n{self.summary}"
        elif self.notes:
            system += "\n\nNotes:\n" + "\n".join(f"- {fact}" for fact in self.notes)
        return [{"role": "system", "content": system}, *self.messages]

    def clear(self) -> int:
        names = {
            call["id"]: call["function"]["name"]
            for message in self.messages
            for call in message.get("tool_calls") or []
        }
        results = [message for message in self.messages if message["role"] == "tool"]
        cleared = 0
        for message in results[self.keep :]:
            line = CLEARED.format(name=names.get(message["tool_call_id"], "the tool"))
            if message["content"] != line:
                message["content"] = line
                cleared += 1
        return cleared

    def compact(self, client: httpx.Client) -> bool:
        starts = [
            i for i, message in enumerate(self.messages) if message["role"] == "user"
        ]
        if len(starts) <= self.turns:
            return False
        cut = max(len(self.messages) - 4 * self.turns, 0)
        lines = (
            [f"Summary of the conversation before: {self.summary}"]
            if self.summary
            else []
        )
        for message in self.messages[:cut]:
            if message["role"] == "user":
                lines.append(f"Caller: {message['content']}")
            elif message["role"] == "assistant" and message.get("content"):
                lines.append(f"Assistant: {message['content']}")
        body = {
            "model": MODEL,
            "messages": [
                {"role": "user", "content": f"{SUMMARISE}\n\n" + "\n\n".join(lines)}
            ],
            "max_tokens": 300,
        }
        response = client.post("/chat/completions", json=body)
        response.raise_for_status()
        self.summary = response.json()["choices"][0]["message"].get("content") or ""
        self.messages = self.messages[cut:]
        return True

    def fit(self, client: httpx.Client) -> str | None:
        if self.used <= self.budget:
            return None
        if self.clear():
            return "cleared"
        if self.compact(client):
            return "summarised"
        return None
