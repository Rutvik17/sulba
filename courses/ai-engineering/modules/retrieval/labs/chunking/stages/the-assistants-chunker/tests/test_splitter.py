import pytest

from splitter import places, split, windows


@pytest.mark.id("tst_qgmhws")
def test_windows():
    """A block in windows of words"""
    assert windows("one two  three four five", 2) == ["one two", "three four", "five"]
    assert windows("one two", 5) == ["one two"]


@pytest.mark.id("tst_cia150")
def test_long_block():
    """A block too long for a chunk, cut into windows"""
    text = "# Apply\n\none two three four five six"
    assert split(text, 4) == ["# Apply", "one two three four", "five six"]


@pytest.mark.id("tst_wsyf59")
def test_places():
    """Each chunk's place in the page"""
    text = "# Apply\n\nApply online.\n\nOr by phone."
    assert places(text, ["# Apply", "Apply online.\n\nOr by phone."]) == [
        (0, 7),
        (9, 36),
    ]
