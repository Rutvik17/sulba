import pytest

from costs import costs


@pytest.mark.id("tst_4jnlov")
def test_gpt2_small():
    """GPT-2 small on its whole context"""
    assert costs(50257, 1024, 768, 12, 12, 1024) == {
        "parameters": 124_439_808,
        "forward": 142_406_400,
        "training": 427_219_200,
    }


@pytest.mark.id("tst_5j1l38")
def test_whole_numbers():
    """Whole numbers"""
    found = costs(1000, 64, 48, 3, 6, 50)
    assert sorted(found) == ["forward", "parameters", "training"]
    assert all(type(value) is int for value in found.values())
