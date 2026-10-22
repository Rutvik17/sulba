"""The desk's conversations in Postgres, on connections from a pool: a conversation started,
read with its messages in order, and each turn kept with what it used, all of it or none."""

import secrets
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
        conversation = Conversation(
            id=secrets.token_urlsafe(16), page=page, messages=[]
        )
        with self.pool.connection() as conn:
            conn.execute(
                "INSERT INTO conversations (id, page) VALUES (%s, %s)",
                [conversation.id, page],
            )
        return conversation

    def get(self, conversation_id: str) -> Conversation | None:
        """The conversation with its messages in order, or None."""
        with self.pool.connection() as conn, conn.transaction():
            found = conn.execute(
                "SELECT page FROM conversations WHERE id = %s", [conversation_id]
            ).fetchone()
            if found is None:
                return None
            rows = conn.execute(
                "SELECT role, content FROM messages WHERE conversation_id = %s "
                "ORDER BY position",
                [conversation_id],
            ).fetchall()
        messages = [Message(role=role, content=content) for role, content in rows]
        return Conversation(id=conversation_id, page=found[0], messages=messages)

    def keep(
        self, conversation_id: str, usage: Usage, messages: Sequence[Message] = ()
    ) -> None:
        """Keeps a turn: what it used and the messages it added after the conversation's last,
        all in one transaction. KeyError when there's no such conversation."""
        with self.pool.connection() as conn, conn.transaction():
            # The conversation's row stays locked until the transaction ends, so two turns
            # kept at once take their positions one after the other.
            found = conn.execute(
                "SELECT 1 FROM conversations WHERE id = %s FOR UPDATE",
                [conversation_id],
            ).fetchone()
            if found is None:
                raise KeyError(conversation_id)
            count = conn.execute(
                "SELECT count(*) FROM messages WHERE conversation_id = %s",
                [conversation_id],
            ).fetchone()[0]
            with conn.cursor() as cursor:
                cursor.executemany(
                    "INSERT INTO messages (conversation_id, position, role, content) "
                    "VALUES (%s, %s, %s, %s)",
                    [
                        (conversation_id, count + n, message.role, message.content)
                        for n, message in enumerate(messages)
                    ],
                )
            conn.execute(
                "INSERT INTO turns (conversation_id, started_at, seconds, prompt_tokens, "
                "completion_tokens, outcome) VALUES (%s, %s, %s, %s, %s, %s)",
                [
                    conversation_id,
                    usage.started_at,
                    usage.seconds,
                    usage.prompt_tokens,
                    usage.completion_tokens,
                    usage.outcome,
                ],
            )
