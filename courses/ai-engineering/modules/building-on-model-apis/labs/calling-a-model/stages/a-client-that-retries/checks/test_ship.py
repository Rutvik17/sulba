import httpx
import pytest

from chat import ModelError
from retry import GaveUp, ask_within

QUESTION = [{"role": "user", "content": "When do you open on Saturday?"}]


def most():
    return 1.0


def least():
    return 0.0


@pytest.mark.id("tst_f9cgur")
def test_retries_what_may_pass(model, loop):
    """Asks again after each failure that may pass"""
    model.fails(503, "Loading model")
    model.fails(429, "Too many requests.")
    model.fails(500, "Internal error")
    model.disconnects()
    model.hangs()
    model.says("We open at 9 on Saturdays.")
    reply = loop.run_until_complete(
        ask_within(model.async_client(), QUESTION, 64, 120, timeout=10, jitter=most)
    )
    assert reply.text == "We open at 9 on Saturdays."
    assert len(model.requests) == 6


@pytest.mark.id("tst_3hr478")
def test_never_retries_what_cant_pass(model, loop):
    """Never asks again after an error the same request will get again"""
    for status, message in [
        (400, "Expected 'messages' to be an array"),
        (401, "Invalid API Key"),
        (404, "File Not Found"),
    ]:
        model.fails(status, message)
        with pytest.raises(ModelError) as raised:
            loop.run_until_complete(ask_within(model.async_client(), QUESTION, 64, 30))
        assert (raised.value.status, raised.value.message) == (status, message)
    assert len(model.requests) == 3 and loop.time() == 0


@pytest.mark.id("tst_zybxgk")
def test_waits(model, loop):
    """Waits as long as the server asks, and otherwise longer each time"""
    started = []

    def answer(request):
        started.append(loop.time())
        if len(started) == 1:
            model.fails(429, "Too many requests.", retry_after=3)
        elif len(started) < 6:
            model.fails(503, "Loading model")
        else:
            model.says("We open at 9 on Saturdays.")

    model.answers(answer)
    loop.run_until_complete(
        ask_within(model.async_client(), QUESTION, 64, 60, jitter=most)
    )
    assert started == [0, 3, 5, 9, 17, 25]


@pytest.mark.id("tst_4ihpft")
def test_jitter(model, loop):
    """Spreads its own waits by the random factor, and not the server's"""
    started = []

    def answer(request):
        started.append(loop.time())
        if len(started) == 1:
            model.fails(429, "Too many requests.", retry_after=2)
        elif len(started) < 4:
            model.fails(500, "Internal error")
        else:
            model.says("We open at 9 on Saturdays.")

    model.answers(answer)
    loop.run_until_complete(
        ask_within(model.async_client(), QUESTION, 64, 60, jitter=least)
    )
    assert started == [0, 2, 3, 5]


@pytest.mark.id("tst_bxsc6k")
def test_deadline(model, loop):
    """Gives up by the deadline, and never waits past it"""
    model.answers(lambda request: model.hangs())
    client = model.async_client()
    with pytest.raises(GaveUp) as raised:
        loop.run_until_complete(
            ask_within(client, QUESTION, 64, 30, timeout=10, jitter=most)
        )
    assert isinstance(raised.value.__cause__, httpx.TimeoutException)
    assert loop.time() <= 30
    hung = loop.time()
    model.answers(
        lambda request: model.fails(429, "Too many requests.", retry_after=40)
    )
    with pytest.raises(GaveUp) as raised:
        loop.run_until_complete(
            ask_within(model.async_client(), QUESTION, 64, 30, jitter=most)
        )
    assert isinstance(raised.value.__cause__, ModelError)
    assert loop.time() == hung
