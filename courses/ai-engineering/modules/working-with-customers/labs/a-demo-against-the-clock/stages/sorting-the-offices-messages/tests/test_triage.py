import pytest

from triage import MODEL, QUEUES, triage


def sent(model):
    """The messages of each request the model received."""
    return [request.body["messages"] for request in model.requests]


@pytest.mark.id("tst_rss312")
def test_the_briefs_example(model):
    """Files a message to the queue the model names"""
    model.says('{"queue": "benefits"}')
    message = "My retirement payment didn't arrive this month."
    assert triage(model.client(), message) == "benefits"
    (request,) = model.requests
    assert request.path.endswith("/chat/completions")
    assert request.body["model"] == MODEL
    system, user = request.body["messages"]
    assert system["role"] == "system" and user == {"role": "user", "content": message}
    assert all(queue in system["content"] for queue in QUEUES)


@pytest.mark.id("tst_2ng476")
def test_only_the_offices_queues(model):
    """Asks again when the model names a queue the office doesn't have"""
    model.says('{"queue": "pensions"}')
    model.says('{"queue": "veterans"}')
    assert (
        triage(model.client(), "Is my GI Bill housing paid this month?") == "veterans"
    )
    assert len(model.requests) == 2
    model.says('{"queue": "agent"}')
    assert triage(model.client(), "Where do I park?") == "agent"


@pytest.mark.id("tst_kbe9nu")
def test_asked_once_more(model):
    """Asks once more after a reply it can't read, and files a second to the agent"""
    model.says("The licences queue.")
    model.says('{"queue": "licences"')
    assert triage(model.client(), "My licence expires next week.") == "agent"
    assert len(model.requests) == 2
    assert sent(model)[0] == sent(model)[1]


@pytest.mark.id("tst_jtgghk")
def test_json_in_a_code_block(model):
    """Reads JSON inside a Markdown code block"""
    model.says('```json\n{"queue": "licences"}\n```')
    assert triage(model.client(), "How do I renew my ID card?") == "licences"
    model.says('```\n{"queue": "student-aid"}\n```')
    assert triage(model.client(), "When is my loan payment due?") == "student-aid"


@pytest.mark.id("tst_sxd6gu")
def test_numbers_removed(model):
    """Sends a Social Security number as [number removed], however it's written"""
    message = (
        "My number is 123-45-6789, my wife's is 987 65 4321 and my son's 111223333."
        " Call me on 555-123-4567."
    )
    model.says('{"queue": "benefits"}')
    triage(model.client(), message)
    content = sent(model)[0][-1]["content"]
    assert content == (
        "My number is [number removed], my wife's is [number removed] and my son's"
        " [number removed]. Call me on 555-123-4567."
    )


@pytest.mark.id("tst_06iv4n")
def test_the_model_down(model):
    """Files the message to the agent when the model fails or doesn't answer"""
    model.fails(503, "Loading model")
    assert triage(model.client(), "Where's my disability check?") == "agent"
    model.hangs()
    assert triage(model.client(), "Where's my disability check?") == "agent"
    model.disconnects()
    assert triage(model.client(), "Where's my disability check?") == "agent"
    assert len(model.requests) == 3
