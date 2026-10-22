import pytest

from desk_memory import CLEARED, DeskMemory

CLEAR = CLEARED.format(name="search_help")


def call(n, i=0):
    return {
        "id": f"call_{n}_{i}",
        "type": "function",
        "function": {"name": "search_help", "arguments": "{}"},
    }


def searched(n, calls=1, content=None):
    """A turn whose model searches calls times at once, then replies."""
    return [
        {"role": "user", "content": f"Question {n}"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [call(n, i) for i in range(calls)],
        },
        *[
            {
                "role": "tool",
                "tool_call_id": f"call_{n}_{i}",
                "content": content or f"Passages {n}",
            }
            for i in range(calls)
        ],
        {"role": "assistant", "content": f"Answer {n}"},
    ]


def memory_of(*turns, **options):
    memory = DeskMemory("You help.", 1000, **options)
    for each in turns:
        for message in each:
            memory.add(message)
    return memory


def results(memory):
    return [m["content"] for m in memory.messages if m["role"] == "tool"]


@pytest.mark.id("tst_9mvsts")
def test_the_oldest_go(model):
    """Clearing takes the oldest results and keeps the most recent"""
    memory = memory_of(*(searched(n) for n in range(1, 5)))
    memory.count({"prompt_tokens": 2000, "completion_tokens": 0})
    memory.fit(model.client())
    assert results(memory) == [CLEAR, CLEAR, "Passages 3", "Passages 4"]


@pytest.mark.id("tst_gtmot0")
def test_the_reply_counts(model):
    """A request is over the budget by its prompt and its reply together, which the next
    request sends again"""
    memory = memory_of(*(searched(n) for n in range(1, 4)))
    memory.count({"prompt_tokens": 900, "completion_tokens": 200})
    assert memory.fit(model.client()) == "cleared"


@pytest.mark.id("tst_i6kazh")
def test_whole_turns(model):
    """A summary takes whole turns: what's kept starts at a caller's message, and every tool
    result kept has its call"""
    model.says("Earlier questions, answered.")
    memory = memory_of(
        searched(1, calls=2, content=CLEAR),
        searched(2, content=CLEAR),
        searched(3, content=CLEAR),
        [
            {"role": "user", "content": "Thanks"},
            {"role": "assistant", "content": "You're welcome."},
        ],
    )
    assert memory.compact(model.client())
    assert memory.messages[0] == {"role": "user", "content": "Question 3"}
    called = set()
    for message in memory.messages:
        called |= {each["id"] for each in message.get("tool_calls") or []}
        if message["role"] == "tool":
            assert message["tool_call_id"] in called


@pytest.mark.id("tst_vbys8c")
def test_notes_outlast_summaries(model):
    """The notes stay in the system message once the conversation is summarised"""
    model.says("Earlier questions, answered.")
    memory = memory_of(*(searched(n, content=CLEAR) for n in range(1, 4)))
    memory.note("They can take calls in the morning.")
    memory.compact(model.client())
    system = memory.request()[0]["content"]
    assert "- They can take calls in the morning." in system
    assert system.endswith("Earlier questions, answered.")
