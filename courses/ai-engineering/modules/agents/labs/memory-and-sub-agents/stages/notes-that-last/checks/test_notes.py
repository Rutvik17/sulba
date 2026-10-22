import pytest

from notebook import Notebook

MORNING = "They can take calls in the morning."
NAME = "Their name is Ana."


def opened(folder, caller="c-101"):
    return Notebook(folder).open(caller, "You help.", 8000)


@pytest.mark.id("tst_hpukeh")
def test_notes_come_back(tmp_path):
    """Each conversation starts with the caller's notes from every one before, in the order
    they were saved, and a note already held isn't kept twice"""
    opened(tmp_path).note(MORNING)
    second = opened(tmp_path)
    assert second.note(NAME) == "Noted."
    assert second.note(MORNING) != "Noted."
    third = opened(tmp_path)
    assert third.notes == [MORNING, NAME]
    assert third.request()[0]["content"] == (
        f"You help.\n\nNotes:\n- {MORNING}\n- {NAME}"
    )


@pytest.mark.id("tst_1cep11")
def test_callers_apart(tmp_path):
    """No caller's notes reach another's conversation, whatever their id, and the notes stay
    in the notebook's folder"""
    folder = tmp_path / "notes"
    opened(folder, "a").note(MORNING)
    for caller in ["b", "../a", "./a", "a/", "A", "", "notes/a"]:
        assert opened(folder, caller).notes == []
        opened(folder, caller).note(f"Note for {caller!r}.")
    assert opened(folder, "a").notes == [MORNING]
    assert [path.name for path in tmp_path.iterdir()] == ["notes"]
    assert all(path.parent == folder for path in folder.rglob("*"))


@pytest.mark.id("tst_fgtagp")
def test_forgotten_for_good(tmp_path):
    """A note the caller asks the desk to forget is gone from this conversation and the next,
    and a note that isn't held gets an error that lists the notes there are"""
    memory = opened(tmp_path)
    memory.note(MORNING)
    memory.note(NAME)
    assert memory.forget(MORNING) == "Forgotten."
    assert MORNING not in memory.request()[0]["content"]
    assert opened(tmp_path).notes == [NAME]
    wrong = opened(tmp_path).forget("They live in Ohio.")
    assert wrong.startswith("Error:") and NAME in wrong
    assert opened(tmp_path).notes == [NAME]


@pytest.mark.id("tst_a4u6qn")
def test_a_small_notebook(tmp_path):
    """A caller holds at most 20 notes of at most 200 characters, and a note past either gets
    an error and isn't kept"""
    memory = opened(tmp_path)
    for n in range(20):
        assert memory.note(f"Note {n}.") == "Noted."
    full = memory.note("One more.")
    assert full.startswith("Error:")
    assert opened(tmp_path).notes == [f"Note {n}." for n in range(20)]
    memory.forget("Note 0.")
    long = memory.note("x" * 201)
    assert long.startswith("Error:")
    assert memory.note("x" * 200) == "Noted."
    assert len(opened(tmp_path).notes) == 20
