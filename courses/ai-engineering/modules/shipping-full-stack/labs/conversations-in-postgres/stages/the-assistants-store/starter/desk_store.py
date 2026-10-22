"""The desk's conversations in Postgres, by the assistant."""

import secrets
from collections.abc import Sequence

from psycopg_pool import ConnectionPool

from conversations import Conversation, Message, Page
from store import Usage


class DeskStore:
    def __init__(self, pool: ConnectionPool) -> None:
        self.pool = pool

    def start(self, page: Page | None) -> Conversation:
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
        conn = self.pool.getconn()
        found = conn.execute(
            f"SELECT page FROM conversations WHERE id = '{conversation_id}'"
        ).fetchone()
        if found is None:
            return None
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE conversation_id = %s "
            "ORDER BY position",
            [conversation_id],
        ).fetchall()
        self.pool.putconn(conn)
        messages = [Message(role=role, content=content) for role, content in rows]
        return Conversation(id=conversation_id, page=found[0], messages=messages)

    def keep(
        self, conversation_id: str, usage: Usage, messages: Sequence[Message] = ()
    ) -> None:
        with self.pool.connection() as conn, conn.transaction():
            count = conn.execute(
                "SELECT count(*) FROM messages WHERE conversation_id = %s",
                [conversation_id],
            ).fetchone()[0]
            found = conn.execute(
                "SELECT 1 FROM conversations WHERE id = %s FOR UPDATE",
                [conversation_id],
            ).fetchone()
            if found is None:
                raise KeyError(conversation_id)
            with conn.cursor() as cursor:
                cursor.executemany(
                    "INSERT INTO messages (conversation_id, position, role, content) "
                    "VALUES (%s, %s, %s, %s)",
                    [
                        (conversation_id, count + n, message.role, message.content)
                        for n, message in enumerate(messages)
                    ],
                )
        with self.pool.connection() as conn:
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
