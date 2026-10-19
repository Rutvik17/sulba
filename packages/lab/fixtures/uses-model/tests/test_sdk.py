import openai
import pytest


def client(model):
    return openai.OpenAI(
        base_url=model.url, api_key="test", http_client=model.client(), max_retries=0
    )


@pytest.mark.id("tst_mdl013")
def test_reply(model):
    """Gives the openai package the reply it expects"""
    model.says("We open at 9.", usage=(12, 5))
    reply = client(model).chat.completions.create(
        model="shop", messages=[{"role": "user", "content": "When do you open?"}]
    )
    assert reply.choices[0].message.content == "We open at 9."
    assert (reply.usage.prompt_tokens, reply.usage.completion_tokens) == (12, 5)
    assert model.requests[0].headers["authorization"] == "Bearer test"


@pytest.mark.id("tst_mdl014")
def test_stream(model):
    """Streams tool calls that the openai package puts back together"""
    calls = [("hours", ['{"day":', '"Monday"}']), ("book", {"bikes": 2})]
    model.says("Let me look.", tool_calls=calls)
    model.says("Let me look.", tool_calls=calls)
    shop = client(model)
    messages = [{"role": "user", "content": "Book two bikes on Monday"}]
    whole = shop.chat.completions.create(model="shop", messages=messages)
    with shop.chat.completions.stream(model="shop", messages=messages) as stream:
        rebuilt = stream.get_final_completion()

    def calls(reply):
        return [
            (call.id, call.function.name, call.function.arguments)
            for call in reply.choices[0].message.tool_calls
        ]

    assert calls(whole) == [
        ("call_1", "hours", '{"day":"Monday"}'),
        ("call_2", "book", '{"bikes":2}'),
    ]
    assert calls(rebuilt) == [
        ("call_3", "hours", '{"day":"Monday"}'),
        ("call_4", "book", '{"bikes":2}'),
    ]
    assert rebuilt.choices[0].message.content == whole.choices[0].message.content
    assert rebuilt.choices[0].finish_reason == whole.choices[0].finish_reason == "tool_calls"
    assert model.requests[1].body["stream"] is True


@pytest.mark.id("tst_mdl015")
def test_errors(model):
    """Gives the openai package errors it reads"""
    model.fails(429, "Too many requests.", retry_after=2)
    with pytest.raises(openai.RateLimitError) as raised:
        client(model).chat.completions.create(model="shop", messages=[])
    assert raised.value.status_code == 429
    assert raised.value.body == {"code": 429, "message": "Too many requests."}
    assert raised.value.response.headers["retry-after"] == "2"
