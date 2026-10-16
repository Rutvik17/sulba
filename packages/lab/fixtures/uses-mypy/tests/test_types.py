import pytest


@pytest.mark.id("tst_mypy01")
def test_typed(typecheck):
    """Finds nothing wrong in typed code"""
    assert typecheck("boxes.py") == []


@pytest.mark.id("tst_mypy02")
def test_errors(typecheck):
    """Gives each error mypy finds, with the file it imports checked too"""
    assert typecheck("labels.py") == [
        "labels.py:4: error: Function is missing a type annotation  [no-untyped-def]",
        'labels.py:9: error: Incompatible return value type (got "float", expected "str")'
        "  [return-value]",
    ]


@pytest.mark.id("tst_mypy03")
def test_fails(typecheck):
    """Fails when the code has errors"""
    assert typecheck("labels.py") == []
