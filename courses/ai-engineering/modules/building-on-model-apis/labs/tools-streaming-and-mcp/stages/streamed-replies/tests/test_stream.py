import json

import httpx
import pytest
from openai import OpenAI
from openai.lib.streaming.chat import ChatCompletionStreamState

from stream import MODEL, ModelError, Streamed, stream

QUESTION = [{"role": "user", "content": "When are you open on Saturday?"}]
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "opening_hours",
            "description": "The shop's opening hours on a day of the week.",
            "parameters": {
                "type": "object",
                "properties": {"day": {"type": "string"}},
                "required": ["day"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }
]


def reference(model, tools=None):
    """The same reply as the openai package puts its stream back together. Its replies were
    scripted second, so its calls' ids are numbered as the first's were."""
    client = OpenAI(base_url=model.url, api_key="none", http_client=model.client())
    state = ChatCompletionStreamState()
    chunks = client.chat.completions.create(
        model=MODEL,
        messages=QUESTION,
        stream=True,
        stream_options={"include_usage": True},
        **({"tools": tools} if tools else {}),
    )
    for chunk in chunks:
        state.handle_chunk(chunk)
    completion = state.current_completion_snapshot
    choice = completion.choices[0]
    calls = [
        {
            "id": f"call_{number}",
            "type": "function",
            "function": {
                "name": call.function.name,
                "arguments": call.function.arguments,
            },
        }
        for number, call in enumerate(choice.message.tool_calls or [], 1)
    ]
    usage = completion.usage.model_dump(
        include={"prompt_tokens", "completion_tokens", "total_tokens"}
    )
    return Streamed(choice.message.content or "", calls, choice.finish_reason, usage)


def replying(body):
    """A client whose server answers every request with body, as a stream's bytes."""
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=body))
    return httpx.Client(base_url="http://model.test/v1", transport=transport)


@pytest.mark.id("tst_syb76u")
def test_request(model):
    """The request asks for a stream, with the tokens used at its end"""
    model.says("We open at 9.")
    stream(model.client(), QUESTION)
    body = model.requests[0].body
    assert body["model"] == MODEL and body["messages"] == QUESTION
    assert body["stream"] is True
    assert body["stream_options"] == {"include_usage": True}
    assert "tools" not in body


@pytest.mark.id("tst_68ypj6")
def test_text(model):
    """The text arrives in pieces, each handed on as it comes, and the whole is the openai package's"""
    pieces = ["We open ", "at 9:00 ", "on Saturdays", ", and close at 13:00."]
    for _ in range(2):
        model.says(*pieces, usage=(19, 14))
    seen = []
    found = stream(model.client(), QUESTION, on_text=seen.append)
    assert seen == pieces
    assert found == reference(model)
    assert found.text == "".join(pieces) and found.usage["total_tokens"] == 33


@pytest.mark.id("tst_41xhlm")
def test_tool_calls(model):
    """Tool calls are put back together from their pieces, each under its index"""
    calls = [
        ("opening_hours", ['{"day"', ': "Sat', 'urday"}']),
        ("opening_hours", ['{"day": ', '"Sunday"}']),
    ]
    for _ in range(2):
        model.says("Let me check.", tool_calls=calls, usage=(80, 30))
    found = stream(model.client(), QUESTION, TOOLS)
    assert model.requests[0].body["tools"] == TOOLS
    assert found == reference(model, TOOLS)
    assert [json.loads(call["function"]["arguments"]) for call in found.tool_calls] == [
        {"day": "Saturday"},
        {"day": "Sunday"},
    ]
    assert found.finish_reason == "tool_calls"


@pytest.mark.id("tst_2vkbnh")
def test_cut_off(model):
    """A reply cut off at its limit says so"""
    for _ in range(2):
        model.says("We open at", finish_reason="length", usage=(19, 3))
    found = stream(model.client(), QUESTION)
    assert found == reference(model)
    assert found.finish_reason == "length"


@pytest.mark.id("tst_s824vv")
def test_lines(model):
    """A line ends only at CR LF, LF or CR, so a line separator inside a reply stays in it"""
    for _ in range(2):
        model.says("Mill Lane Bristol", "\u0085done")
    found = stream(model.client(), QUESTION)
    assert found == reference(model)
    assert found.text == "Mill Lane Bristol\u0085done"


@pytest.mark.id("tst_aiqs5p")
def test_event_stream():
    """Comments, CR LF and CR line ends, and data split over several lines are read as the
    server-sent events format reads them"""
    events = [
        ": keep-alive",
        "",
        'data: {"choices": [{"index": 0, "delta": {"content": "We open"}, '
        '"finish_reason": null}]}',
        "",
        'data:{"choices": [{"index": 0, "delta": {"content": " at 9"},',
        'data: "finish_reason": null}]}',
        "",
        'data: {"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}',
        "",
        "data: [DONE]",
        "",
    ]
    for end in ["\r\n", "\r"]:
        client = replying(end.join(events).encode())
        assert stream(client, QUESTION) == Streamed("We open at 9", [], "stop", None)


@pytest.mark.id("tst_3dl6xn")
def test_errors(model):
    """An error the API answers with is raised with its status and message"""
    model.fails(503, "Loading model")
    with pytest.raises(ModelError) as raised:
        stream(model.client(), QUESTION)
    assert (raised.value.status, raised.value.message) == (503, "Loading model")
