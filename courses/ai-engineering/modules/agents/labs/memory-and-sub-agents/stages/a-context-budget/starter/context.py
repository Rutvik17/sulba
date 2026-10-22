"""A conversation's messages kept within a budget of tokens, by clearing old tool results."""

from typing import Any

CLEARED = "Cleared to keep the conversation short. Call {name} again to see it."


class Context:
    """The messages an agent sends, after its system message, and the tokens its last request
    took, prompt and reply, as the server counted them. Over the budget, the oldest tool results
    are cleared, all but the keep most recent, each to a line that says how to see it again."""

    def __init__(self, system: str, budget: int, keep: int = 2) -> None:
        self.system = system
        self.budget = budget
        self.keep = keep
        self.messages: list[dict[str, Any]] = []
        self.used = 0

    def add(self, message: dict[str, Any]) -> None:
        self.messages.append(message)

    def count(self, usage: dict[str, int]) -> None:
        """Keeps the size of the request just answered: its prompt and its reply, which the next
        request sends again."""
        raise NotImplementedError

    def request(self) -> list[dict[str, Any]]:
        """The messages the next request sends, its system message first."""
        raise NotImplementedError

    def clear(self) -> int:
        """Clears every tool result but the keep most recent, and gives how many it cleared that
        weren't cleared before."""
        raise NotImplementedError

    def fit(self) -> int:
        """Before a request: when the last one was over the budget, clears old tool results.
        Gives how many it cleared."""
        raise NotImplementedError
