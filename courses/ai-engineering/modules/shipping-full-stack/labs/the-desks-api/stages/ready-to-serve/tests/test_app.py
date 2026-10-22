import json

import pytest
from httpx import ASGITransport, AsyncClient

from app import Settings, create_app, settings_from

SETTINGS = Settings(
    model_url="http://127.0.0.1:9931/v1", running=1, waiting=8, seconds=120
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


@pytest.mark.id("tst_wgn2he")
def test_a_conversation(loop, model):
    """The app starts a conversation and replies in it"""
    model.says("We open at 9.")
    app = create_app(SETTINGS, client=model.async_client(timeout=300))

    async def work(client):
        started = (await client.post("/conversations", json={"page": "dmv"})).json()
        path = f"/conversations/{started['id']}/messages"
        return await client.post(path, json={"content": "When do you open?"})

    reply = serving(loop, app, work)
    assert events(reply.text)[-1] == ("done", {"content": "We open at 9."})


@pytest.mark.id("tst_wbq74p")
def test_health(loop, model):
    """The health check says the app is up"""
    app = create_app(SETTINGS, client=model.async_client())

    async def work(client):
        return await client.get("/health")

    response = serving(loop, app, work)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.id("tst_k5vjv8")
def test_settings_from_the_environment():
    """Each setting comes from its variable, or its default"""
    assert settings_from({}) == SETTINGS
    chosen = settings_from(
        {"DESK_RUNNING": "3", "DESK_MODEL_URL": "http://10.0.0.5:8080/v1"}
    )
    assert (chosen.running, chosen.model_url) == (3, "http://10.0.0.5:8080/v1")
