import json

import httpx
import pytest
from assistant import ask, pieces
from openai import OpenAI


def client(handler):
    """The OpenAI client, sending each request to handler instead of over the network."""
    return OpenAI(
        base_url="http://model.test/v1",
        api_key="test",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


@pytest.mark.id("tst_oai001")
def test_reply():
    """Sends a chat request and reads its reply"""
    sent = []

    def handler(request):
        sent.append((request.url.path, json.loads(request.content)))
        reply = {
            "id": "chatcmpl-1",
            "object": "chat.completion",
            "created": 0,
            "model": "shop",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "We open at 9."},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17},
        }
        return httpx.Response(200, json=reply)

    assert ask(client(handler), "When do you open?") == "We open at 9."
    message = {"role": "user", "content": "When do you open?"}
    assert sent == [
        ("/v1/chat/completions", {"messages": [message], "model": "shop", "temperature": 0})
    ]


@pytest.mark.id("tst_oai002")
def test_stream():
    """Reads a streamed reply as it comes"""
    events = [
        {"role": "assistant", "content": ""},
        {"content": "We open"},
        {"content": " at 9."},
    ]
    chunks = [
        {
            "id": "chatcmpl-2",
            "object": "chat.completion.chunk",
            "created": 0,
            "model": "shop",
            "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
        }
        for delta in events
    ]
    body = "".join(f"data: {json.dumps(chunk)}\n\n" for chunk in chunks) + "data: [DONE]\n\n"

    def handler(request):
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=body)

    assert list(pieces(client(handler), "When do you open?")) == ["We open", " at 9."]
