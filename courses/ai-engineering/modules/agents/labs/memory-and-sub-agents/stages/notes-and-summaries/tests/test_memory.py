import pytest

from context import CLEARED
from memory import MODEL, NOTE, SUMMARISE, Agent, Memory


def turn(n, cleared=False):
    """A caller's message, the model's search and its result, and the model's reply."""
    result = CLEARED.format(name="search_help") if cleared else f"Passages {n}"
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
        {"role": "tool", "tool_call_id": f"call_{n}", "content": result},
        {"role": "assistant", "content": f"Answer {n} [p{n}]"},
    ]


def memory_of(turns, cleared=True, **options):
    memory = Memory("You help.", 1000, **options)
    for n in range(1, turns + 1):
        for message in turn(n, cleared):
            memory.add(message)
    return memory


def over(memory):
    memory.count({"prompt_tokens": 1500, "completion_tokens": 20})


@pytest.mark.id("tst_wh5jv0")
def test_notes():
    """A note is kept, and the system message lists each note after the system prompt"""
    memory = memory_of(1)
    assert memory.note(" They can take calls in the morning. ") == "Noted."
    memory.note("Their name is Ana.")
    assert memory.request()[0] == {
        "role": "system",
        "content": "You help.\n\nNotes:\n- They can take calls in the morning.\n"
        "- Their name is Ana.",
    }
    assert memory.request()[1:] == memory.messages


@pytest.mark.id("tst_312mld")
def test_clearing_first(model):
    """Over the budget, a tool result left to clear is cleared, and nothing is summarised"""
    memory = memory_of(4, cleared=False)
    over(memory)
    assert memory.fit(model.client()) == "cleared"
    assert model.requests == []
    assert memory.summary == ""


@pytest.mark.id("tst_i2qyv4")
def test_a_summary(model):
    """With nothing left to clear, the turns before the last two are summarised in one request
    of the caller's messages and the model's replies, and the summary takes their place"""
    model.says("They asked about cards and claims; cited p1 and p2.", usage=(300, 20))
    memory = memory_of(4)
    over(memory)
    assert memory.fit(model.client()) == "summarised"
    [request] = model.requests
    assert request.body["model"] == MODEL
    [asked] = request.body["messages"]
    assert asked["role"] == "user"
    assert asked["content"] == (
        f"{SUMMARISE}\n\nCaller: Question 1\n\nAssistant: Answer 1 [p1]\n\n"
        "Caller: Question 2\n\nAssistant: Answer 2 [p2]"
    )
    assert memory.messages == turn(3, True) + turn(4, True)
    assert memory.request()[0]["content"] == (
        "You help.\n\nThe conversation before the messages below, summarised:\n"
        "They asked about cards and claims; cited p1 and p2."
    )


@pytest.mark.id("tst_46l22y")
def test_notes_stay(model):
    """Notes outlast a summary: they stay in the system message, before the summary"""
    model.says("Earlier questions, answered.")
    memory = memory_of(3)
    memory.note("They can take calls in the afternoon.")
    over(memory)
    memory.fit(model.client())
    assert memory.request()[0]["content"] == (
        "You help.\n\nNotes:\n- They can take calls in the afternoon.\n\n"
        "The conversation before the messages below, summarised:\n"
        "Earlier questions, answered."
    )


@pytest.mark.id("tst_3i06eb")
def test_summaries_build(model):
    """A second summary is written from the first and the turns since, and replaces it"""
    model.says("First summary.")
    model.says("Second summary.")
    memory = memory_of(3)
    over(memory)
    memory.fit(model.client())
    for message in turn(4, True):
        memory.add(message)
    over(memory)
    assert memory.fit(model.client()) == "summarised"
    asked = model.requests[1].body["messages"][0]["content"]
    assert asked == (
        f"{SUMMARISE}\n\nSummary of the conversation before: First summary.\n\n"
        "Caller: Question 2\n\nAssistant: Answer 2 [p2]"
    )
    assert memory.summary == "Second summary."
    assert memory.messages == turn(3, True) + turn(4, True)


@pytest.mark.id("tst_uun2dd")
def test_too_few_turns(model):
    """A conversation of no more turns than it keeps has nothing to summarise: no request is
    sent and nothing changes"""
    memory = memory_of(2)
    over(memory)
    assert memory.fit(model.client()) is None
    assert model.requests == []
    assert memory.messages == turn(1, True) + turn(2, True)


@pytest.mark.id("tst_c6h5e5")
def test_the_agent_notes(model):
    """The agent offers note with its tools, and a note the model saves reaches the next
    request's system message"""
    model.says(tool_calls=[("note", {"fact": "They can take calls in the morning."})])
    model.says("Noted: mornings.")
    model.says("Hello again.")
    agent = Agent(model.client(), Memory("You help.", 8000), [], lambda n, a: "")
    assert agent.reply("I can only take calls in the morning.") == "Noted: mornings."
    first, second = model.requests
    assert first.body["tools"] == [NOTE]
    [result] = [m for m in second.body["messages"] if m["role"] == "tool"]
    assert result["content"] == "Noted."
    assert (
        "Notes:\n- They can take calls in the morning."
        in (second.body["messages"][0]["content"])
    )
    agent.reply("Hi")
    assert (
        "- They can take calls in the morning."
        in (model.requests[2].body["messages"][0]["content"])
    )
