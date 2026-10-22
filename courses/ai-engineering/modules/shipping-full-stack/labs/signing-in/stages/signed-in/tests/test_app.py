import json
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app import Settings, create_app, settings_from


def settings(database, identity, public_url="https://desk.test"):
    return Settings(
        model_url="http://127.0.0.1:9931/v1",
        database_url=database,
        running=1,
        waiting=8,
        seconds=120,
        issuer=identity.issuer,
        client_id=identity.client_id,
        client_secret=identity.client_secret,
        public_url=public_url,
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
    """Runs work(browser) against the app, between its start and its stop, with a browser
    that keeps the app's cookies."""

    async def go():
        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="https://desk.test"
            ) as browser:
                return await work(browser)

    return loop.run_until_complete(go())


async def sign_in(browser, identity, name="ada"):
    started = await browser.get("/auth/sign-in")
    return await browser.get(identity.sign_in(started.headers["location"], name))


async def converse(browser, content="When do you open?"):
    """A new conversation with one message in it, and the reply."""
    started = (await browser.post("/conversations", json={})).json()["id"]
    reply = await browser.post(
        f"/conversations/{started}/messages", json={"content": content}
    )
    return started, reply


def made(database, identity, model):
    return create_app(
        settings(database, identity),
        client=model.async_client(timeout=300),
        identity=identity.async_client(),
    )


@pytest.mark.id("tst_5qdzay")
def test_settings_from_the_environment():
    """The provider, the desk's id and secret there, and the database come from their
    variables, and the rest have their defaults"""
    chosen = settings_from(
        {
            "DESK_DATABASE_URL": "postgresql://desk:secret@db:5432/desk",
            "DESK_ISSUER": "https://accounts.example.com",
            "DESK_CLIENT_ID": "desk",
            "DESK_CLIENT_SECRET": "a-long-secret",
        }
    )
    assert chosen.issuer == "https://accounts.example.com"
    assert chosen.client_id == "desk"
    assert chosen.client_secret.get_secret_value() == "a-long-secret"
    assert chosen.public_url == "http://127.0.0.1:8000"
    assert (chosen.running, chosen.waiting, chosen.seconds) == (1, 8, 120)


@pytest.mark.id("tst_9u7nwh")
def test_a_person_signs_in_and_converses(loop, database, identity, model):
    """A person signs in, starts a conversation and has a reply, and the app knows them"""
    model.says("We open at 9.")
    app = made(database, identity, model)

    async def work(browser):
        await sign_in(browser, identity, "grace")
        started, reply = await converse(browser)
        kept = (await browser.get(f"/conversations/{started}")).json()
        return reply, kept, (await browser.get("/me")).json()

    reply, kept, me = serving(loop, app, work)
    assert events(reply.text)[-1] == ("done", {"content": "We open at 9."})
    assert [m["content"] for m in kept["messages"]] == [
        "When do you open?",
        "We open at 9.",
    ]
    assert (me["email"], me["name"]) == ("grace@example.com", "Grace")


@pytest.mark.id("tst_iog1yg")
def test_nothing_without_signing_in(loop, database, identity, model):
    """Without signing in, starting a conversation and reading the usage are refused"""
    app = made(database, identity, model)

    async def work(browser):
        return [
            (await browser.post("/conversations", json={})).status_code,
            (await browser.get("/usage")).status_code,
            (await browser.get("/me")).status_code,
        ]

    assert serving(loop, app, work) == [403, 403, 403]


@pytest.mark.id("tst_0ibicl")
def test_todays_usage(loop, database, identity, model):
    """Today's usage counts the person's turn just kept"""
    model.says("We open at 9.", usage=(700, 30))
    app = made(database, identity, model)

    async def work(browser):
        await sign_in(browser, identity)
        await converse(browser)
        return (await browser.get("/usage")).json()

    (today,) = serving(loop, app, work)
    assert today["day"] == datetime.now(UTC).date().isoformat()
    assert (today["turns"], today["done"]) == (1, 1)
    assert (today["prompt_tokens"], today["completion_tokens"]) == (700, 30)
