import asyncio

import httpx
import pytest

from shop import ask, ask_soon, ask_until_answered, events


@pytest.mark.id("tst_mdl001")
def test_reply(model):
    """Answers with the reply the test scripted, and keeps the request"""
    model.says("We open at 9.")
    assert ask(model.client(), "When do you open?") == "We open at 9."
    [request] = model.requests
    assert (request.method, request.path) == ("POST", "/v1/chat/completions")
    assert request.headers["content-type"] == "application/json"
    assert request.body == {
        "model": "shop",
        "messages": [{"role": "user", "content": "When do you open?"}],
    }


@pytest.mark.id("tst_mdl002")
def test_reply_form(model):
    """Replies in the chat completions API's form"""
    model.says("We open", " at 9.", usage=(12, 5))
    reply = model.client().post("/chat/completions", json={"messages": []}).json()
    assert reply == {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": 0,
        "model": "scripted",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "We open at 9."},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17},
    }


@pytest.mark.id("tst_mdl003")
def test_stream(model):
    """Streams a reply in its pieces, as server-sent events"""
    model.says("We open", " at 9.", usage=(12, 5))
    found = events(model.client(), "When do you open?")
    assert found[-1] == "[DONE]"
    assert [event["choices"] for event in found[:-1]] == [
        [{"index": 0, "delta": {"role": "assistant", "content": None}, "finish_reason": None}],
        [{"index": 0, "delta": {"content": "We open"}, "finish_reason": None}],
        [{"index": 0, "delta": {"content": " at 9."}, "finish_reason": None}],
        [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        [],
    ]
    assert found[-2]["usage"] == {"prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17}
    assert {event["object"] for event in found[:-1]} == {"chat.completion.chunk"}


@pytest.mark.id("tst_mdl004")
def test_tool_calls(model):
    """Calls tools, each with its own id"""
    model.says(tool_calls=[("hours", {"day": "Monday"}), ("book", '{"bikes": 2}')])
    model.says(tool_calls=[("hours", {"day": "Tuesday"})], finish_reason="length")
    client = model.client()
    first = client.post("/chat/completions", json={"messages": []}).json()["choices"][0]
    assert first["finish_reason"] == "tool_calls"
    assert first["message"] == {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "hours", "arguments": '{"day":"Monday"}'},
            },
            {
                "id": "call_2",
                "type": "function",
                "function": {"name": "book", "arguments": '{"bikes": 2}'},
            },
        ],
    }
    second = client.post("/chat/completions", json={"messages": []}).json()["choices"][0]
    assert second["finish_reason"] == "length"
    assert second["message"]["tool_calls"][0]["id"] == "call_3"


@pytest.mark.id("tst_mdl005")
def test_streamed_tool_call(model):
    """Streams a tool call's name, then its arguments in their pieces"""
    model.says("Let me look.", tool_calls=[("hours", ['{"day":', '"Monday"}'])])
    found = events(model.client(), "When do you open on Monday?")
    deltas = [event["choices"][0]["delta"] for event in found[1:-3]]
    assert deltas == [
        {"content": "Let me look."},
        {
            "tool_calls": [
                {"index": 0, "id": "call_1", "type": "function", "function": {"name": "hours"}}
            ]
        },
        {"tool_calls": [{"index": 0, "function": {"arguments": '{"day":'}}]},
        {"tool_calls": [{"index": 0, "function": {"arguments": '"Monday"}'}}]},
    ]
    assert found[-3]["choices"][0]["finish_reason"] == "tool_calls"


@pytest.mark.id("tst_mdl006")
def test_errors(model):
    """Fails with a status, a message and a Retry-After, as llama-server words an error"""
    model.fails(429, "Too many requests.", retry_after=2)
    model.fails(503, "Loading model")
    client = model.client()
    busy = client.post("/chat/completions", json={"messages": []})
    assert busy.status_code == 429
    assert busy.headers["retry-after"] == "2"
    assert busy.json() == {"error": {"code": 429, "message": "Too many requests."}}
    loading = client.post("/chat/completions", json={"messages": []})
    assert "retry-after" not in loading.headers
    assert loading.json() == {
        "error": {"code": 503, "message": "Loading model", "type": "unavailable_error"}
    }


@pytest.mark.id("tst_mdl007")
def test_refusals(model):
    """Refuses what llama-server refuses, before any reply the test scripted"""
    model.says("Hello.")
    client = model.client()
    wrong = [
        client.get("/models"),
        client.post("/chat/completions", json={"prompt": "Hello"}),
        client.post("/chat/completions", json={"messages": "Hello"}),
        client.post("/chat/completions", json={"messages": [{"role": "user"}]}),
        client.post("/chat/completions", json={"messages": [{"role": "assistant"}]}),
        client.post("/chat/completions", content=b"{"),
    ]
    assert [(response.status_code, response.json()["error"]["type"]) for response in wrong] == [
        (404, "not_found_error"),
        *[(400, "invalid_request_error")] * 5,
    ]
    assert [response.json()["error"]["message"] for response in wrong[:5]] == [
        "File Not Found",
        "'messages' is required",
        "Expected 'messages' to be an array",
        "All non-assistant messages must contain 'content'",
        "Assistant message must contain either 'content' or 'tool_calls'!",
    ]
    assert len(model.requests) == 6
    assert ask(client, "Hi") == "Hello."


@pytest.mark.id("tst_mdl008")
def test_time(loop, model):
    """Takes as long as the test says, on the loop's clock"""
    model.says("Hello.", after=1.5)
    model.says("Hello again.", after=3)
    client = model.async_client()
    assert loop.run_until_complete(ask_soon(client, "Hi")) == "Hello."
    assert loop.time() == 1.5
    with pytest.raises(httpx.ReadTimeout):
        loop.run_until_complete(ask_soon(client, "Hi"))
    assert loop.time() == 3.5


@pytest.mark.id("tst_mdl009")
def test_hangs(loop, model):
    """Never answers, until the client's timeout ends"""
    model.hangs()
    model.hangs()
    model.hangs()
    with pytest.raises(httpx.ReadTimeout):
        loop.run_until_complete(ask_soon(model.async_client(), "Hi"))
    assert loop.time() == 2
    with pytest.raises(httpx.ReadTimeout):
        ask(model.client(timeout=5), "Hi")
    assert loop.time() == 2

    async def wait():
        async with asyncio.timeout(10):
            await model.async_client(timeout=None).post("/chat/completions", json={"messages": []})

    with pytest.raises(TimeoutError):
        loop.run_until_complete(wait())
    assert loop.time() == 12


@pytest.mark.id("tst_mdl010")
def test_disconnects(model):
    """Drops a connection without a reply"""
    model.disconnects()
    with pytest.raises(httpx.RemoteProtocolError):
        ask(model.client(), "Hi")


@pytest.mark.id("tst_mdl011")
def test_answers(model):
    """Answers each request from a function, once the scripted replies run out"""
    model.says("Hello.")

    def shout(request):
        model.says(request.body["messages"][-1]["content"].upper())

    model.answers(shout)
    client = model.client()
    assert [ask(client, text) for text in ["Hi", "open?", "bye"]] == ["Hello.", "OPEN?", "BYE"]


@pytest.mark.id("tst_mdl012")
def test_no_reply_left(model):
    """Stops code that asks for more replies than the test scripted"""
    model.fails(500, "Out of memory")
    ask_until_answered(model.client(), "Hi")
