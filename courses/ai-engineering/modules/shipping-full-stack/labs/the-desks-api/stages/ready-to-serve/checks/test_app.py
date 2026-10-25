import asyncio
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


@pytest.mark.id("tst_wu9h5s")
def test_settings_that_do_not_fit():
    """Settings that don't fit are refused, each by its variable's name"""
    with pytest.raises(ValueError) as refused:
        settings_from(
            {"DESK_RUNNING": "0", "DESK_SECONDS": "soon", "DESK_MODEL_URL": "desk:9931"}
        )
    message = str(refused.value)
    for name in ("DESK_RUNNING", "DESK_SECONDS", "DESK_MODEL_URL"):
        assert name in message
    assert "DESK_WAITING" not in message


@pytest.mark.id("tst_s63kn4")
def test_one_client_to_the_model(loop):
    """The app makes one client to the model from its settings, waits for each reply as long as
    its limit, and closes the client as it stops"""
    app = create_app(SETTINGS)

    async def work(client):
        model = app.state.client
        assert str(model.base_url) == "http://127.0.0.1:9931/v1/"
        assert model.timeout.read == 120
        assert app.state.agents.make(None).client is model
        assert app.state.agents.make("ssa").client is model
        return model

    model = serving(loop, app, work)
    assert model.is_closed


@pytest.mark.id("tst_18ec7u")
def test_the_help_pages_load_once(loop, model):
    """Every conversation's agent works on one desk, with every help page loaded as the app
    starts"""
    app = create_app(SETTINGS, client=model.async_client())

    async def work(client):
        first, second = app.state.agents.make(None), app.state.agents.make("dmv")
        assert first.actions.desk is second.actions.desk
        return len(first.actions.desk.search.passages)

    assert serving(loop, app, work) == 2419


@pytest.mark.id("tst_bd75zi")
def test_health_while_busy(loop, model):
    """The health check answers at once while the desk is replying, without asking the model"""
    model.says("We open at 9.", after=60)
    app = create_app(SETTINGS, client=model.async_client(timeout=300))

    async def work(client):
        started = (await client.post("/conversations", json={})).json()
        path = f"/conversations/{started['id']}/messages"
        reply = asyncio.ensure_future(client.post(path, json={"content": "When?"}))
        await asyncio.sleep(1)
        health = await client.get("/health")
        answered = loop.time()
        await reply
        return health, answered

    health, answered = serving(loop, app, work)
    assert health.status_code == 200
    assert answered < 2
    assert len(model.requests) == 1
