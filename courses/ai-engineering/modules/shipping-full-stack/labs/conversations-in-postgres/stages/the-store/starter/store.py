"""The desk's conversations in Postgres, on connections from a pool: a conversation started,
read with its messages in order, and each turn kept with what it used, all of it or none."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from psycopg_pool import ConnectionPool

from conversations import Conversation, Message, Page

Outcome = Literal["done", "too long", "failed", "left"]


@dataclass(frozen=True)
class Usage:
    """What a turn used: when it started, how long it took, its tokens of prompt and of reply,
    and how it ended."""

    started_at: datetime
    seconds: float
    prompt_tokens: int
    completion_tokens: int
    outcome: Outcome


class Store:
    """Every conversation, in the database the pool connects to. The pool's connections are in
    autocommit mode, so each method's work is a transaction only where it says so."""

    def __init__(self, pool: ConnectionPool) -> None:
        self.pool = pool

    def start(self, page: Page | None) -> Conversation:
        """A new conversation, with an id no one can guess."""
        raise NotImplementedError

    def get(self, conversation_id: str) -> Conversation | None:
        """The conversation with its messages in order, or None."""
        raise NotImplementedError

    def keep(
        self, conversation_id: str, usage: Usage, messages: Sequence[Message] = ()
    ) -> None:
        """Keeps a turn: what it used and the messages it added after the conversation's last,
        all in one transaction. KeyError when there's no such conversation."""
        raise NotImplementedError
