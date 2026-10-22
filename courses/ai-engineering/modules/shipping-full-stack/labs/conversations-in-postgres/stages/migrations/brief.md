The desk keeps its conversations in memory, so a restart loses them, and two copies of the app each see their own. This lab keeps them in Postgres. It gives you `conversations.py` and `gate.py` as you wrote them in The desk's API, and `desk.py` and `agent.py` as before. The agent now counts the tokens each turn has used, in `prompt_tokens` and `completion_tokens`.

A database's schema changes as the app does, and every copy of the app, on every machine, must reach the same schema. In `migrations.py`, each change is a `Migration`: a version, a name and its SQL. `MIGRATIONS` holds the first, `conversations`. Add two more:

- `2`, `messages`: each message's conversation, which it refers to and goes with when the conversation is deleted; its position in the conversation, from 0; its role, `caller` or `desk`; and its content. A conversation has one message at each position.
- `3`, `turns`: each turn's id, made by the database; its conversation, as for messages; when it started; its seconds; its tokens of prompt and of reply, none of them below 0; and its outcome, `done`, `too long`, `failed` or `left`. An index named `turns_started_at` on when each turn started.

```
messages: conversation_id text, position integer, role text, content text
turns: id bigint, conversation_id text, started_at timestamptz, seconds double precision,
       prompt_tokens integer, completion_tokens integer, outcome text
```

No column may be empty except a conversation's page. Then write `migrate(conn, migrations=MIGRATIONS)`. It takes a connection in autocommit mode, applies each migration not yet applied, and gives the versions it applied:

- The versions go 1, 2, 3 and so on, in order. Anything else raises `MigrationError` before the database is touched.
- `schema_migrations` records each migration applied: its version, name, checksum and when it was applied. The table is made the first time.
- Each migration runs in a transaction of its own, with its record. One that fails changes nothing, and the ones before it stay applied.
- A migration whose checksum differs from the one recorded raises `MigrationError`: `Migration 3, turns, has changed since it was applied: add a new migration instead.`
- Two apps that migrate at once take turns, through Postgres's advisory lock on `LOCK`, so each migration is applied once. The lock is released however `migrate` ends.

```
migrate(conn, migrations=MIGRATIONS) -> list[int]
```

`uv run sulba.py db` starts the lab's database for your own code, at the address it prints, until you press Ctrl+C. The tests start a database of their own.
