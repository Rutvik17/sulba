"""The shop's assistant's calls to its model, through the chat completions API."""

from dataclasses import dataclass

import httpx

MODEL = "Qwen3.5-0.8B"


@dataclass(frozen=True)
class Reply:
    """What the model wrote: its text, why it stopped, and the tokens it read and wrote."""

    text: str
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int


class ModelError(Exception):
    """An error the API answered with: its HTTP status and its message."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"{status}: {message}")
        self.status = status
        self.message = message


def ask(client: httpx.Client, messages: list[dict[str, str]], max_tokens: int) -> Reply:
    """The model's reply to messages, in at most max_tokens tokens. Raises ModelError when the
    API answers with an error."""
    raise NotImplementedError
