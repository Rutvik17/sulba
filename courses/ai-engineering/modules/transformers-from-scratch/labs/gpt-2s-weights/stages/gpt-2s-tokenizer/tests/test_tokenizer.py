import json
from pathlib import Path

import pytest

from tokenizer import END, byte_characters, decode, encode, load

RECORDED = json.loads(Path("references/tokens.json").read_text())["texts"]


@pytest.fixture(scope="module")
def gpt2():
    return load("data")


@pytest.mark.id("tst_16mkts")
def test_byte_characters(gpt2):
    """A character for every byte, each of them a token"""
    vocabulary, _ = gpt2
    characters = byte_characters()
    assert sorted(characters) == list(range(256))
    assert len(set(characters.values())) == 256
    assert characters[ord("A")] == "A"
    assert characters[0xE9] == "é"
    assert characters[ord(" ")] == "Ġ"
    assert characters[ord("\n")] == "Ċ"
    assert characters[0] == "Ā"
    assert all(character in vocabulary for character in characters.values())


@pytest.mark.id("tst_n0lpkw")
def test_load(gpt2):
    """GPT-2's vocabulary and merges, in their order"""
    vocabulary, merges = gpt2
    assert len(vocabulary) == 50257
    assert sorted(vocabulary.values()) == list(range(50257))
    assert vocabulary[END] == 50256
    assert len(merges) == 50000
    assert merges[0] == ("Ġ", "t")
    assert all(isinstance(pair, tuple) and len(pair) == 2 for pair in merges)


@pytest.mark.id("tst_wq2unq")
def test_encode(gpt2):
    """Each text's tokens, as tiktoken gives them"""
    vocabulary, merges = gpt2
    for recorded in RECORDED:
        assert encode(recorded["text"], vocabulary, merges) == recorded["tokens"]


@pytest.mark.id("tst_87swe7")
def test_separator(gpt2):
    """The separator as one token, wherever it is"""
    vocabulary, merges = gpt2
    tokens = encode(f"{END}a{END}{END}b{END}", vocabulary, merges)
    assert tokens.count(50256) == 4
    assert tokens[0] == tokens[2] == tokens[3] == tokens[-1] == 50256


@pytest.mark.id("tst_01vzap")
def test_decode(gpt2):
    """The text back from its tokens, and U+FFFD for a character cut short"""
    vocabulary, merges = gpt2
    for recorded in RECORDED:
        assert decode(recorded["tokens"], vocabulary) == recorded["text"]
    smile = encode("🙂", vocabulary, merges)
    assert len(smile) > 1
    assert decode(smile[:1], vocabulary) == "�"
