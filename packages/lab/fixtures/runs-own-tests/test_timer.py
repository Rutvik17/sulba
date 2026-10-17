from timer import answer_after


def test_answers(loop):
    assert loop.run_until_complete(answer_after(60, "done")) == "done"


def test_waits(loop):
    loop.run_until_complete(answer_after(60, "done"))
    assert loop.time() == 60
