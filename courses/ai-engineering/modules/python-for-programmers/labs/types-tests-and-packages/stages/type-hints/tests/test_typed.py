import math
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from typed import Failure, check_number, explain, failures, label


def probe(typecheck, name, code):
    """What mypy says about a file of code that uses typed.py."""
    Path(name).write_text(code, encoding="utf-8")
    return typecheck(name)


@pytest.mark.id("tst_wi1987")
def test_failure():
    """Holds a failure's path and message, unchangeable"""
    failure = Failure(("radius",), "Expected a number, but received: '17.99'")
    assert failure.path == ("radius",)
    assert failure.message == "Expected a number, but received: '17.99'"
    with pytest.raises(FrozenInstanceError):
        failure.message = "changed"


@pytest.mark.id("tst_t8pgez")
def test_explain():
    """Explains a failure, with its path when it has one"""
    assert explain(Failure((), "Expected an object")) == "Expected an object"
    assert explain(Failure(("samples", 2, "radius"), "Expected a number")) == (
        "At path: samples.2.radius -- Expected a number"
    )


@pytest.mark.id("tst_oieqk6")
def test_check_number():
    """Checks a number as superstruct does"""
    assert check_number(17.99) is None
    assert check_number(3) is None
    assert check_number("17.99") == "Expected a number, but received: '17.99'"
    assert check_number(True) == "Expected a number, but received: True"
    assert check_number(math.nan) == "Expected a number, but received: nan"
    assert check_number(None) == "Expected a number, but received: None"


@pytest.mark.id("tst_rjfw48")
def test_label():
    """Labels a sample, with its note when it has one"""
    assert label({"id": "S00001", "radius": 17.99}) == "S00001 (17.99)"
    assert label({"id": "S00002", "radius": 20.57, "note": "repeat"}) == (
        "S00002 (20.57): repeat"
    )


@pytest.mark.id("tst_aka5e5")
def test_failures():
    """Finds each field a sample can't hold"""
    assert failures({"id": "S00001", "radius": 17.99}) == []
    assert (
        failures({"id": "S00002", "radius": 20.57, "note": "repeat", "seen": 2}) == []
    )
    assert failures({"id": 7, "radius": "17.99", "note": None}) == [
        Failure(("id",), "Expected a string, but received: 7"),
        Failure(("radius",), "Expected a number, but received: '17.99'"),
        Failure(("note",), "Expected a string, but received: None"),
    ]
    assert failures({}) == [
        Failure(("id",), "Expected a string, but received: None"),
        Failure(("radius",), "Expected a number, but received: None"),
    ]


@pytest.mark.id("tst_hwx6n4")
def test_strict(typecheck):
    """Passes mypy --strict"""
    assert typecheck("typed.py") == []


@pytest.mark.id("tst_46g1ia")
def test_types(typecheck):
    """Gives each function the types asked for"""
    code = (
        "from typed import Failure, check_number, explain, failures, label\n"
        "\n"
        "reveal_type(Failure)\n"
        "reveal_type(explain)\n"
        "reveal_type(check_number)\n"
        "reveal_type(label)\n"
        "reveal_type(failures)\n"
    )
    assert probe(typecheck, "types_probe.py", code) == [
        'types_probe.py:3: note: Revealed type is "def (path: builtins.tuple[builtins.str |'
        ' builtins.int, ...], message: builtins.str) -> typed.Failure"',
        'types_probe.py:4: note: Revealed type is "def (failure: typed.Failure) ->'
        ' builtins.str"',
        'types_probe.py:5: note: Revealed type is "def (value: builtins.object) ->'
        ' builtins.str | None"',
        "types_probe.py:6: note: Revealed type is \"def (sample: TypedDict('typed.Sample',"
        " {'id': builtins.str, 'radius': builtins.float, 'note'?: builtins.str})) ->"
        ' builtins.str"',
        'types_probe.py:7: note: Revealed type is "def (record: builtins.dict[builtins.str,'
        ' builtins.object]) -> builtins.list[typed.Failure]"',
    ]


@pytest.mark.id("tst_koi6nd")
def test_mistakes(typecheck):
    """Lets mypy catch a caller's mistakes"""
    code = (
        "from typed import Sample, explain, label\n"
        "\n"
        'explain("radius")\n'
        'label({"id": "S00001"})\n'
        'sample: Sample = {"id": "S00001", "radius": 17.99}\n'
        'sample["texture"]\n'
    )
    assert probe(typecheck, "mistakes_probe.py", code) == [
        'mistakes_probe.py:3: error: Argument 1 to "explain" has incompatible type "str";'
        ' expected "Failure"  [arg-type]',
        'mistakes_probe.py:4: error: Missing key "radius" for TypedDict "Sample"'
        "  [typeddict-item]",
        'mistakes_probe.py:6: error: TypedDict "Sample" has no key "texture"'
        "  [typeddict-item]",
    ]
