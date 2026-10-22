In `store.py`, write `Store`, which keeps the conversations in Postgres in place of The desk's API's `Conversations`. It works on a `ConnectionPool` from psycopg_pool, whose connections are in autocommit mode:

- `start(page)` keeps a new conversation, with an id no one can guess, and gives it.
- `get(conversation_id)` gives the conversation, with its messages in order, or `None`.
- `keep(conversation_id, usage, messages=())` keeps a turn: its `Usage`, as a row of `turns`, and the messages the turn added, after the conversation's last. All of it is kept, or none of it. A conversation that isn't there raises `KeyError`. When two turns are kept at once in one conversation, each keeps its messages together, one turn after the other.

Every value goes to Postgres as a parameter, and none is written into the SQL. The conversations' routes take the store from `app.state.conversations` and use it as they used `Conversations`.

```
Store(pool).start(page) -> Conversation
Store(pool).get(conversation_id) -> Conversation | None
Store(pool).keep(conversation_id, usage, messages=()) -> None
```

The tests run on your migrations, in a database of their own.
