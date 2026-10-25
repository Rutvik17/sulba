import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from conversations import Conversations, Message, install, router


def make_app():
    app = FastAPI()
    install(app)
    app.include_router(router)
    app.state.conversations = Conversations()
    return app


def send(loop, app, method, path, body=None):
    async def request():
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://desk.test"
        ) as client:
            return await client.request(method, path, json=body)

    return loop.run_until_complete(request())


@pytest.mark.id("tst_g45f0n")
def test_starting_a_conversation(loop):
    """A new conversation, with its address, from the help pages it's opened from"""
    app = make_app()
    response = send(loop, app, "POST", "/conversations", {"page": "dmv"})
    assert response.status_code == 201
    started = response.json()
    assert response.headers["location"] == f"/conversations/{started['id']}"
    assert started["page"] == "dmv" and started["messages"] == []
    other = send(loop, app, "POST", "/conversations", {}).json()
    assert other["page"] is None
    assert other["id"] != started["id"]
    assert len(started["id"]) >= 22


@pytest.mark.id("tst_cyewu4")
def test_getting_a_conversation(loop):
    """A conversation with its messages, and a problem details object for one that isn't there"""
    app = make_app()
    started = send(loop, app, "POST", "/conversations", {"page": "va"}).json()
    app.state.conversations.add(started["id"], Message(role="caller", content="Hello"))
    got = send(loop, app, "GET", f"/conversations/{started['id']}")
    assert got.status_code == 200
    assert got.json()["messages"] == [{"role": "caller", "content": "Hello"}]
    missing = send(loop, app, "GET", "/conversations/nope")
    assert missing.status_code == 404
    assert missing.headers["content-type"] == "application/problem+json"
    assert missing.json() == {
        "type": "about:blank",
        "title": "Not Found",
        "status": 404,
        "detail": "There's no conversation with this id.",
    }


@pytest.mark.id("tst_k5nl57")
def test_a_body_that_does_not_fit(loop):
    """A body that doesn't fit gets a 422 whose errors point at each field that's wrong"""
    app = make_app()
    response = send(
        loop, app, "POST", "/conversations", {"page": "irs", "topic": "tax"}
    )
    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    found = response.json()
    assert found["title"] == "Unprocessable Content"
    assert sorted(error["pointer"] for error in found["errors"]) == [
        "#/page",
        "#/topic",
    ]
    assert all(error["detail"] for error in found["errors"])


@pytest.mark.id("tst_rrrgnl")
def test_routes_that_are_not_there(loop):
    """An address or a method the app doesn't have gets a problem details object too"""
    app = make_app()
    nowhere = send(loop, app, "GET", "/tickets")
    assert nowhere.status_code == 404
    assert nowhere.json() == {
        "type": "about:blank",
        "title": "Not Found",
        "status": 404,
    }
    wrong = send(loop, app, "DELETE", "/conversations")
    assert wrong.status_code == 405
    assert wrong.json()["title"] == "Method Not Allowed"
    assert wrong.headers["allow"] == "POST"
