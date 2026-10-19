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
    body = {"model": MODEL, "messages": messages, "max_completion_tokens": max_tokens}
    response = client.post("/chat/completions", json=body)
    if response.is_error:
        raise ModelError(response.status_code, error_message(response))
    reply = response.json()
    choice, usage = reply["choices"][0], reply["usage"]
    return Reply(
        text=choice["message"]["content"] or "",
        finish_reason=choice["finish_reason"],
        prompt_tokens=usage["prompt_tokens"],
        completion_tokens=usage["completion_tokens"],
    )


def error_message(response: httpx.Response) -> str:
    """The message of the error in the response's JSON, or the response's text when it has
    none."""
    try:
        return response.json()["error"]["message"]
    except ValueError, KeyError, TypeError:
        return response.text
