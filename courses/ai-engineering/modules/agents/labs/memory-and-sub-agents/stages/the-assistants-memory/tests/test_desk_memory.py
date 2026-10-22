import pytest

from desk_memory import CLEARED, SUMMARISE, DeskMemory


def turn(n):
    return [
        {"role": "user", "content": f"Question {n}"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": f"call_{n}",
                    "type": "function",
                    "function": {"name": "search_help", "arguments": "{}"},
                }
            ],
        },
        {"role": "tool", "tool_call_id": f"call_{n}", "content": f"Passages {n}"},
        {"role": "assistant", "content": f"Answer {n} [p{n}]"},
    ]


def memory_of(turns, **options):
    memory = DeskMemory("You help.", 1000, **options)
    for n in range(1, turns + 1):
        for message in turn(n):
            memory.add(message)
    return memory


@pytest.mark.id("tst_0sah9y")
def test_notes(model):
    """The model's notes are listed in the system message"""
    memory = memory_of(1)
    assert memory.note("They can take calls in the morning.") == "Noted."
    assert memory.request()[0]["content"] == (
        "You help.\n\nNotes:\n- They can take calls in the morning."
    )


@pytest.mark.id("tst_jfwakc")
def test_under_the_budget(model):
    """Within the budget, nothing is cleared or summarised"""
    memory = memory_of(3)
    memory.count({"prompt_tokens": 600, "completion_tokens": 0})
    assert memory.fit(model.client()) is None
    assert model.requests == []


@pytest.mark.id("tst_fyat7n")
def test_clearing(model):
    """Over the budget, a tool result beyond the two kept is cleared"""
    memory = memory_of(3)
    memory.count({"prompt_tokens": 1200, "completion_tokens": 0})
    assert memory.fit(model.client()) == "cleared"
    results = [m["content"] for m in memory.messages if m["role"] == "tool"]
    assert results.count(CLEARED.format(name="search_help")) == 1


@pytest.mark.id("tst_qebbbf")
def test_a_summary(model):
    """Once there is nothing left to clear, the turns before the last two are summarised"""
    model.says("Asked about cards [p1].")
    memory = memory_of(3)
    memory.count({"prompt_tokens": 1200, "completion_tokens": 0})
    memory.fit(model.client())
    assert memory.fit(model.client()) == "summarised"
    [request] = model.requests
    assert request.body["messages"][0]["content"].startswith(SUMMARISE)
    assert [m.get("content") for m in memory.messages if m["role"] == "user"] == [
        "Question 2",
        "Question 3",
    ]
    assert memory.request()[0]["content"].endswith("Asked about cards [p1].")
