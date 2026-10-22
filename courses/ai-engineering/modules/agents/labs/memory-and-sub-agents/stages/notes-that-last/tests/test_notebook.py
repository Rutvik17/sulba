import pytest

from notebook import Notebook

MORNING = "They can take calls in the morning."


@pytest.mark.id("tst_vj1ihi")
def test_a_note(tmp_path):
    """A caller's note is listed in their conversation's system message"""
    memory = Notebook(tmp_path).open("c-101", "You help.", 8000)
    assert memory.note(MORNING) == "Noted."
    assert memory.request()[0]["content"] == f"You help.\n\nNotes:\n- {MORNING}"


@pytest.mark.id("tst_c0a560")
def test_the_next_conversation(tmp_path):
    """The caller's next conversation starts with their notes"""
    Notebook(tmp_path).open("c-101", "You help.", 8000).note(MORNING)
    memory = Notebook(tmp_path).open("c-101", "You help.", 8000)
    assert memory.notes == [MORNING]


@pytest.mark.id("tst_zmdzje")
def test_forgetting(tmp_path):
    """A note the caller asks the desk to forget is gone"""
    memory = Notebook(tmp_path).open("c-101", "You help.", 8000)
    memory.note(MORNING)
    assert memory.forget(MORNING) == "Forgotten."
    assert memory.request()[0]["content"] == "You help."
