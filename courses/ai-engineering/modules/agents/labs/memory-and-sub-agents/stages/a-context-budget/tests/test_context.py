import pytest

from context import CLEARED, Context


def turn(n, tool="search_help"):
    """A caller's message, the model's call of tool and its result, and the model's reply."""
    return [
        {"role": "user", "content": f"Question {n}"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": f"call_{n}",
                    "type": "function",
                    "function": {"name": tool, "arguments": "{}"},
                }
            ],
        },
        {"role": "tool", "tool_call_id": f"call_{n}", "content": f"Result {n}"},
        {"role": "assistant", "content": f"Answer {n} [p{n}]"},
    ]


def context_of(turns, budget=1000, keep=2, tool="search_help"):
    context = Context("You help.", budget, keep)
    for n in range(1, turns + 1):
        for message in turn(n, tool):
            context.add(message)
    return context


def results(context):
    return [m["content"] for m in context.messages if m["role"] == "tool"]


@pytest.mark.id("tst_tf1bzw")
def test_the_request(model):
    """A request sends the system message, then every message added, in order"""
    context = context_of(1)
    assert context.request() == [
        {"role": "system", "content": "You help."},
        *turn(1),
    ]


@pytest.mark.id("tst_0z6pqm")
def test_under_the_budget(model):
    """A conversation whose last request, prompt and reply, was within the budget is left as it
    is"""
    context = context_of(4)
    context.count({"prompt_tokens": 900, "completion_tokens": 100})
    assert context.fit() == 0
    assert results(context) == ["Result 1", "Result 2", "Result 3", "Result 4"]


@pytest.mark.id("tst_q9w4hc")
def test_over_the_budget(model):
    """Over the budget, every tool result but the keep most recent is cleared, oldest first, and
    a cleared result names the tool to call again"""
    context = context_of(4)
    context.count({"prompt_tokens": 900, "completion_tokens": 101})
    assert context.fit() == 2
    cleared = CLEARED.format(name="search_help")
    assert results(context) == [cleared, cleared, "Result 3", "Result 4"]
    assert "search_help" in cleared


@pytest.mark.id("tst_hqgv1x")
def test_calls_stay(model):
    """Clearing keeps each call and its result's place: the model's messages, its calls' ids
    and the replies are all as they were"""
    context = context_of(3, keep=1, tool="list_tickets")
    context.count({"prompt_tokens": 2000, "completion_tokens": 0})
    context.fit()
    for kept, given in zip(context.messages, context_of(3).messages, strict=True):
        if given["role"] == "tool":
            assert kept["tool_call_id"] == given["tool_call_id"]
        else:
            assert kept["role"] == given["role"]
            assert kept["content"] == given["content"]
    assert results(context)[:2] == [CLEARED.format(name="list_tickets")] * 2


@pytest.mark.id("tst_yb0n9x")
def test_cleared_once(model):
    """A result already cleared isn't counted again, and the keep most recent are kept as the
    conversation goes on"""
    context = context_of(3, keep=1)
    context.count({"prompt_tokens": 2000, "completion_tokens": 0})
    assert context.fit() == 2
    for message in turn(4):
        context.add(message)
    context.count({"prompt_tokens": 2000, "completion_tokens": 0})
    assert context.fit() == 1
    assert results(context)[-1] == "Result 4"
    assert results(context).count(CLEARED.format(name="search_help")) == 3
