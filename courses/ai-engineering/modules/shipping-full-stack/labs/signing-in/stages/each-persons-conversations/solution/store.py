"""The desk's conversations in Postgres, on connections from a pool, each one its owner's: a
conversation started, read with its messages in order by its owner alone, each owner's listed,
and each turn kept with what it used, all of it or none."""

import secrets
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from psycopg_pool import ConnectionPool

from conversations import Conversation, Message, Page, Summary
from migrations import Migration

Outcome = Literal["done", "too long", "failed", "left"]

# Each conversation's owner. Those started before anyone signed in have none.
OWNERS = Migration(
    7,
    "owners",
    """
    ALTER TABLE conversations ADD COLUMN owner bigint REFERENCES people ON DELETE CASCADE;
    CREATE INDEX conversations_owner ON conversations (owner, started_at DESC, id);
    """,
)


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

    def start(self, page: Page | None, owner: int) -> Conversation:
        """A new conversation of the owner's, with an id no one can guess."""
        conversation = Conversation(
            id=secrets.token_urlsafe(16), page=page, messages=[]
        )
        with self.pool.connection() as conn:
            conn.execute(
                "INSERT INTO conversations (id, page, owner) VALUES (%s, %s, %s)",
                [conversation.id, page, owner],
            )
        return conversation

    def get(self, conversation_id: str, owner: int) -> Conversation | None:
        """The owner's conversation with its messages in order, or None when there's no such
        conversation or it's someone else's."""
        with self.pool.connection() as conn, conn.transaction():
            found = conn.execute(
                "SELECT page FROM conversations WHERE id = %s AND owner = %s",
                [conversation_id, owner],
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

    def mine(self, owner: int, limit: int = 20) -> list[Summary]:
        """The owner's conversations, the newest first, as many as the limit."""
        with self.pool.connection() as conn:
            rows = conn.execute(
                "SELECT id, page, started_at FROM conversations WHERE owner = %s "
                "ORDER BY started_at DESC, id LIMIT %s",
                [owner, limit],
            ).fetchall()
        return [
            Summary(id=id, page=page, started_at=started_at)
            for id, page, started_at in rows
        ]

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
