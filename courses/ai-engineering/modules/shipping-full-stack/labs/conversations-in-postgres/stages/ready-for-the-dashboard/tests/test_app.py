import json
from datetime import UTC, datetime

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


@pytest.mark.id("tst_8s3gmc")
def test_settings_from_the_environment():
    """The database's address comes from its variable, and the rest have their defaults"""
    chosen = settings_from(
        {"DESK_DATABASE_URL": "postgresql://desk:secret@db:5432/desk"}
    )
    assert chosen.database_url == "postgresql://desk:secret@db:5432/desk"
    assert (chosen.running, chosen.waiting, chosen.seconds) == (1, 8, 120)


@pytest.mark.id("tst_h1x7fd")
def test_a_conversation_on_a_new_database(loop, database, model):
    """The app starts on an empty database and keeps a conversation there"""
    model.says("We open at 9.")
    app = create_app(settings(database), client=model.async_client(timeout=300))

    async def work(client):
        started, reply = await converse(client)
        return reply, (await client.get(f"/conversations/{started}")).json()

    reply, kept = serving(loop, app, work)
    assert events(reply.text)[-1] == ("done", {"content": "We open at 9."})
    assert [m["content"] for m in kept["messages"]] == [
        "When do you open?",
        "We open at 9.",
    ]


@pytest.mark.id("tst_1jwd56")
def test_todays_usage(loop, database, model):
    """Today's usage counts the turn just kept"""
    model.says("We open at 9.", usage=(700, 30))
    app = create_app(settings(database), client=model.async_client(timeout=300))

    async def work(client):
        await converse(client)
        return (await client.get("/usage")).json()

    (today,) = serving(loop, app, work)
    assert today["day"] == datetime.now(UTC).date().isoformat()
    assert (today["turns"], today["done"]) == (1, 1)
    assert (today["prompt_tokens"], today["completion_tokens"]) == (700, 30)
