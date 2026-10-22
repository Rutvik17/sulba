import json
from datetime import UTC, datetime, timedelta

import psycopg
import pytest
from httpx import ASGITransport, AsyncClient

from app import Settings, create_app, settings_from


def settings(database):
    return Settings(
        model_url="http://127.0.0.1:9931/v1",
        database_url=database,
        running=1,
        waiting=8,
        seconds=120,
    )


def events(text):
    found = []
    for block in text.split("\n\n"):
        fields = dict(
            line.split(": ", 1) for line in block.splitlines() if ": " in line
        )
        if "event" in fields:
            found.append((fields["event"], json.loads(fields["data"])))
    return found


def serving(loop, app, work):
    """Runs work(client) against the app, between its start and its stop."""

    async def go():
        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://desk.test"
            ) as client:
                return await work(client)

    return loop.run_until_complete(go())


async def converse(client, content="When do you open?"):
    """A new conversation with one message in it, and the reply."""
    started = (await client.post("/conversations", json={})).json()["id"]
    reply = await client.post(
        f"/conversations/{started}/messages", json={"content": content}
    )
    return started, reply


@pytest.mark.id("tst_aawk9m")
def test_settings_that_do_not_fit():
    """No database, or one that isn't Postgres, is refused by its variable's name"""
    for environ in ({}, {"DESK_DATABASE_URL": "mysql://desk@db/desk"}):
        with pytest.raises(ValueError, match="DESK_DATABASE_URL"):
            settings_from(environ)


@pytest.mark.id("tst_doxggb")
def test_conversations_outlast_the_app(loop, database, model):
    """A conversation kept by one run of the app is there for the next, and each run closes its
    connections as it stops"""
    model.says("We open at 9.")
    first = create_app(settings(database), client=model.async_client(timeout=300))

    async def talk(client):
        started, _ = await converse(client)
        return started

    started = serving(loop, first, talk)
    assert first.state.pool.closed
    second = create_app(settings(database), client=model.async_client(timeout=300))

    async def read(client):
        return (await client.get(f"/conversations/{started}")).json()

    kept = serving(loop, second, read)
    assert [m["role"] for m in kept["messages"]] == ["caller", "desk"]


@pytest.mark.id("tst_j807i7")
def test_each_days_usage(loop, database, model):
    """Each day's turns are counted in UTC, whatever the database's time zone, with their tokens
    and the percentiles of their seconds, for the days asked for"""
    with psycopg.connect(database, autocommit=True) as conn:
        name = conn.info.dbname
        conn.execute(f"ALTER DATABASE \"{name}\" SET timezone TO 'America/New_York'")
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    turns = [
        (today + timedelta(hours=1), 3.0, 100, 10, "done"),
        (today + timedelta(hours=2), 9.0, 300, 30, "too long"),
        (today + timedelta(hours=3), 4.0, 200, 20, "done"),
        (today - timedelta(minutes=30), 12.0, 50, 5, "done"),
        (today - timedelta(days=20), 1.0, 1, 1, "done"),
    ]
    app = create_app(settings(database), client=model.async_client())

    async def work(client):
        with psycopg.connect(database, autocommit=True) as conn:
            conn.execute("INSERT INTO conversations (id) VALUES ('c1')")
            conn.cursor().executemany(
                "INSERT INTO turns (conversation_id, started_at, seconds, prompt_tokens, "
                "completion_tokens, outcome) VALUES ('c1', %s, %s, %s, %s, %s)",
                turns,
            )
        week = (await client.get("/usage")).json()
        month = (await client.get("/usage", params={"days": 30})).json()
        wrong = [
            (await client.get("/usage", params={"days": days})).status_code
            for days in (0, 91)
        ]
        return week, month, wrong

    week, month, wrong = serving(loop, app, work)
    yesterday = (today - timedelta(days=1)).date().isoformat()
    assert week == [
        {
            "day": yesterday,
            "turns": 1,
            "done": 1,
            "prompt_tokens": 50,
            "completion_tokens": 5,
            "p50_seconds": 12.0,
            "p90_seconds": 12.0,
        },
        {
            "day": today.date().isoformat(),
            "turns": 3,
            "done": 2,
            "prompt_tokens": 600,
            "completion_tokens": 60,
            "p50_seconds": 4.0,
            "p90_seconds": 8.0,
        },
    ]
    assert len(month) == 3
    assert wrong == [422, 422]


@pytest.mark.id("tst_q1cvo7")
def test_the_usage_query_uses_the_index(loop, database, model, monkeypatch):
    """The usage query finds a week's turns through the index on when they started, not by
    reading every turn"""
    queries = []
    execute = psycopg.Cursor.execute

    def recorded(cursor, query, params=None, **kwargs):
        if "turns" in str(query) and str(query).lstrip().upper().startswith("SELECT"):
            queries.append((query, params))
        return execute(cursor, query, params, **kwargs)

    app = create_app(settings(database), client=model.async_client())

    async def work(client):
        with psycopg.connect(database, autocommit=True) as conn:
            conn.execute("INSERT INTO conversations (id) VALUES ('c1')")
            conn.execute(
                "INSERT INTO turns (conversation_id, started_at, seconds, prompt_tokens, "
                "completion_tokens, outcome) SELECT 'c1', now() - n * interval '1 hour', "
                "n % 60, 100, 10, 'done' FROM generate_series(1, 20000) AS n"
            )
            conn.execute("ANALYZE turns")
        monkeypatch.setattr(psycopg.Cursor, "execute", recorded)
        response = await client.get("/usage")
        monkeypatch.setattr(psycopg.Cursor, "execute", execute)
        return response

    assert serving(loop, app, work).status_code == 200
    assert queries, "The usage route asked the database nothing about turns."
    with psycopg.connect(database, autocommit=True) as conn:
        for query, params in queries:
            (plan,) = conn.execute(f"EXPLAIN (FORMAT JSON) {query}", params).fetchone()
            nodes = []
            waiting = [plan[0]["Plan"]]
            while waiting:
                node = waiting.pop()
                nodes.append(node)
                waiting += node.get("Plans", [])
            assert not any(
                n["Node Type"] == "Seq Scan" and n.get("Relation Name") == "turns"
                for n in nodes
            )
            assert any(n.get("Index Name") == "turns_started_at" for n in nodes)
