import dataclasses

import pytest

from structs import Failure

MESSAGE = "Expected a number, but received: 'invalid'"


@pytest.mark.id("tst_eepc9b")
def test_fields():
    """Holds a failure's path, type, message and refinement"""
    failure = Failure(("age",), "number", MESSAGE)
    assert failure.path == ("age",)
    assert failure.type == "number"
    assert failure.message == MESSAGE
    assert failure.refinement is None
    sized = Failure((), "string", "Too long", refinement="size")
    assert sized.refinement == "size"


@pytest.mark.id("tst_d34ic2")
def test_equal():
    """Compares failures by their fields"""
    first = Failure(("age",), "number", MESSAGE)
    second = Failure(("age",), "number", MESSAGE)
    assert first == second
    assert first is not second
    assert first != Failure(("height",), "number", MESSAGE)
    assert first != Failure(("age",), "number", MESSAGE, refinement="size")


@pytest.mark.id("tst_a2z0s1")
def test_frozen():
    """Can't be changed once made"""
    failure = Failure(("age",), "number", MESSAGE)
    with pytest.raises(dataclasses.FrozenInstanceError):
        failure.message = "Changed"
    assert failure.message == MESSAGE


@pytest.mark.id("tst_yqa4rj")
def test_set():
    """Goes in a set, once for equal failures"""
    failures = {
        Failure(("age",), "number", MESSAGE),
        Failure(("age",), "number", MESSAGE),
        Failure(("tags", 1), "string", "Expected a string, but received: 3"),
    }
    assert len(failures) == 2


@pytest.mark.id("tst_hkylnv")
def test_key():
    """Gives the key or index of the value that failed"""
    assert Failure(("address", "street"), "string", MESSAGE).key == "street"
    assert Failure(("tags", 1), "string", MESSAGE).key == 1
    assert Failure((), "object", MESSAGE).key is None


@pytest.mark.id("tst_0pcjr2")
def test_explain():
    """Explains itself as superstruct does"""
    assert (
        Failure(("tags", 1), "string", MESSAGE).explain()
        == f"At path: tags.1 -- {MESSAGE}"
    )
    assert Failure((), "number", MESSAGE).explain() == MESSAGE


@pytest.mark.id("tst_yjaorb")
def test_repr():
    """Shows its fields"""
    assert repr(Failure(("age",), "number", "No")) == (
        "Failure(path=('age',), type='number', message='No', refinement=None)"
    )
