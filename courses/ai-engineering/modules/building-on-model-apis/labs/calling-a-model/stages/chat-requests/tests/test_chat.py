import httpx
import pytest

from chat import MODEL, ModelError, Reply, ask

QUESTION = [{"role": "user", "content": "When do you open on Saturday?"}]


@pytest.mark.id("tst_6lb3m3")
def test_request(model):
    """One POST to /chat/completions with the model, the messages and the token limit"""
    model.says("We open at 9.")
    ask(model.client(), QUESTION, 64)
    [request] = model.requests
    assert (request.method, request.path) == ("POST", "/v1/chat/completions")
    assert request.headers["content-type"] == "application/json"
    assert request.body["model"] == MODEL
    assert request.body["messages"] == QUESTION
    assert request.body["max_completion_tokens"] == 64


@pytest.mark.id("tst_1py02d")
def test_reply(model):
    """The reply's text, why it finished and the tokens it took"""
    model.says("We open", " at 9 on Saturdays.", usage=(19, 9))
    found = ask(model.client(), QUESTION, 64)
    assert found == Reply("We open at 9 on Saturdays.", "stop", 19, 9)


@pytest.mark.id("tst_gqbhms")
def test_cut_off(model):
    """A reply cut off at its token limit says so"""
    model.says("A full service includes", finish_reason="length", usage=(19, 4))
    assert ask(model.client(), QUESTION, 4) == Reply(
        "A full service includes", "length", 19, 4
    )


@pytest.mark.id("tst_88ccvx")
def test_tool_call(model):
    """A reply that only calls a tool has no text"""
    model.says(tool_calls=[("opening_hours", {"day": "Saturday"})], usage=(40, 12))
    assert ask(model.client(), QUESTION, 64) == Reply("", "tool_calls", 40, 12)


@pytest.mark.id("tst_xbaoqa")
def test_errors(model):
    """An error's status and the message from its body"""
    model.fails(503, "Loading model")
    with pytest.raises(ModelError) as raised:
        ask(model.client(), QUESTION, 64)
    assert (raised.value.status, raised.value.message) == (503, "Loading model")
    with pytest.raises(ModelError) as raised:
        ask(model.client(), [{"role": "user"}], 64)
    assert raised.value.status == 400
    assert raised.value.message == "All non-assistant messages must contain 'content'"


@pytest.mark.id("tst_pdk0v8")
def test_not_json():
    """An error whose body isn't JSON, such as a proxy's own page"""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(502, text="Bad Gateway")
    )
    client = httpx.Client(base_url="http://model.test/v1", transport=transport)
    with pytest.raises(ModelError) as raised:
        ask(client, QUESTION, 64)
    assert (raised.value.status, raised.value.message) == (502, "Bad Gateway")
