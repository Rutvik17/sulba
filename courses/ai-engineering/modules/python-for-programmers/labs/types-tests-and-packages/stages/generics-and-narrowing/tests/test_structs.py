import math
from pathlib import Path

import pytest

from typed import StructError, array, create, is_, nullable, number, string


def probe(typecheck, name, code):
    """What mypy says about a file of code that uses typed.py."""
    Path(name).write_text(code, encoding="utf-8")
    return typecheck(name)


@pytest.mark.id("tst_yeyjkl")
def test_leaves():
    """Tells strings and numbers apart"""
    assert string().name == "string"
    assert [string().test(value) for value in ["S00001", "", 7, None]] == [
        True,
        True,
        False,
        False,
    ]
    assert number().name == "number"
    assert [number().test(value) for value in [17.99, 3, True, math.nan, "3"]] == [
        True,
        True,
        False,
        False,
        False,
    ]


@pytest.mark.id("tst_zocik3")
def test_array():
    """Checks every item of an array"""
    numbers = array(number())
    assert numbers.name == "array"
    assert numbers.test([17.99, 3])
    assert numbers.test([])
    assert not numbers.test([17.99, "3"])
    assert not numbers.test((17.99, 3))
    assert not numbers.test("17.99")
    assert array(array(string())).test([["a"], [], ["b", "c"]])
    assert not array(array(string())).test([["a"], [7]])


@pytest.mark.id("tst_etcujj")
def test_nullable():
    """Lets None through a nullable struct, and keeps its name"""
    notes = nullable(string())
    assert notes.name == "string"
    assert notes.test(None)
    assert notes.test("repeat")
    assert not notes.test(7)
    assert array(nullable(number())).test([17.99, None])


@pytest.mark.id("tst_emal16")
def test_create_and_is():
    """Creates a value of the struct's type, or raises superstruct's error"""
    assert create([17.99, None], array(nullable(number()))) == [17.99, None]
    assert is_("S00001", string())
    assert not is_(["S00001", 7], array(string()))
    with pytest.raises(StructError) as raised:
        create(["S00001", 7], array(string()))
    assert str(raised.value) == (
        "Expected a value of type `array`, but received: `['S00001', 7]`"
    )
    assert isinstance(raised.value, TypeError)


@pytest.mark.id("tst_yya18p")
def test_strict(typecheck):
    """Passes mypy --strict"""
    assert typecheck("typed.py") == []


@pytest.mark.id("tst_d7cads")
def test_created_types(typecheck):
    """Gives each value create returns its struct's type"""
    code = (
        "from typed import array, create, nullable, number, string\n"
        "\n"
        "reveal_type(create(17.99, number()))\n"
        'reveal_type(create("S00001", nullable(string())))\n'
        "reveal_type(create([], array(nullable(string()))))\n"
        'count: int = create("S00001", string())\n'
    )
    assert probe(typecheck, "created_probe.py", code) == [
        'created_probe.py:3: note: Revealed type is "builtins.float"',
        'created_probe.py:4: note: Revealed type is "builtins.str | None"',
        'created_probe.py:5: note: Revealed type is "builtins.list[builtins.str | None]"',
        "created_probe.py:6: error: Incompatible types in assignment (expression has type"
        ' "str", variable has type "int")  [assignment]',
    ]


@pytest.mark.id("tst_999bud")
def test_narrowed(typecheck):
    """Narrows a value that passes is_, and only one that passes"""
    code = (
        "from typed import array, is_, number, string\n"
        "\n"
        "\n"
        "def show(value: str | int | list[float]) -> None:\n"
        "    if is_(value, string()):\n"
        "        reveal_type(value)\n"
        "    elif is_(value, array(number())):\n"
        "        reveal_type(value)\n"
        "    else:\n"
        "        reveal_type(value)\n"
    )
    assert probe(typecheck, "narrowed_probe.py", code) == [
        'narrowed_probe.py:6: note: Revealed type is "builtins.str"',
        'narrowed_probe.py:8: note: Revealed type is "builtins.list[builtins.float]"',
        'narrowed_probe.py:10: note: Revealed type is "builtins.str | builtins.int |'
        ' builtins.list[builtins.float]"',
    ]
