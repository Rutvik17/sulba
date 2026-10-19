"""What the model reads of a conversation: its text, its tokens, and the conversation cut to fit
the model's window."""

from tokenizers import Tokenizer

# Qwen3.5-0.8B's tokenizer, from its publisher.
TOKENIZER = "data/tokenizer.json"


def prompt(messages: list[dict[str, str]]) -> str:
    """The text Qwen3.5-0.8B reads for messages: each message in its chat template, then the
    start of the assistant's reply, without thinking."""
    raise NotImplementedError


def count(tokenizer: Tokenizer, messages: list[dict[str, str]]) -> int:
    """The tokens the model reads for messages."""
    raise NotImplementedError


def fit(
    tokenizer: Tokenizer, messages: list[dict[str, str]], window: int, reply: int
) -> list[dict[str, str]]:
    """messages without their oldest turns, as few as it takes for them and reply tokens to fit
    in window. A turn is a customer's message with the replies after it, and the system message
    stays. Raises ValueError when the last turn alone doesn't fit."""
    raise NotImplementedError
