import itertools
import random
import string

import pytest
from letters import letter_order

WORDS = 50_000


def sorts(order, words):
    """Whether the order holds every letter of the words once and sorts the words as given."""
    letters = set("".join(words))
    if sorted(order) != sorted(letters):
        return False
    place = {letter: index for index, letter in enumerate(order)}
    keys = [[place[letter] for letter in word] for word in words]
    return keys == sorted(keys)


def some_order(words):
    """Whether some order of the words' letters sorts them, by trying every order."""
    letters = sorted(set("".join(words)))
    return any(
        sorts("".join(order), words) for order in itertools.permutations(letters)
    )


@pytest.mark.id("tst_e3ppun")
def test_letter_order():
    """Finds the order of the alphabet from sorted words"""
    assert letter_order(["wrt", "wrf", "er", "ett", "rftt"]) == "wertf"


@pytest.mark.id("tst_tnu3c0")
def test_edges():
    """Accepts any order the words leave open, and gives "" when none sorts them"""
    assert sorts(letter_order(["ab", "cd"]), ["ab", "cd"])
    assert letter_order(["z"]) == "z"
    assert letter_order([]) == ""
    assert letter_order(["ab", "a"]) == ""
    assert letter_order(["a", "b", "a"]) == ""
    assert letter_order(["a", "ab"]) in ("ab", "ba")
    assert letter_order(["abc", "abc"]) in {
        "".join(p) for p in itertools.permutations("abc")
    }


@pytest.mark.id("tst_qjmoes")
def test_random():
    """Gives an order exactly when trying every order finds one, on random lists"""
    rng = random.Random(202)
    for _ in range(300):
        alphabet = rng.sample("abcde", rng.randint(1, 5))
        place = {letter: index for index, letter in enumerate(alphabet)}
        words = [
            "".join(rng.choices(alphabet, k=rng.randint(1, 4)))
            for _ in range(rng.randint(1, 7))
        ]
        if rng.random() < 0.7:
            words.sort(key=lambda word: [place[letter] for letter in word])
        order = letter_order(words)
        if some_order(words):
            assert sorts(order, words)
        else:
            assert order == ""


@pytest.mark.id("tst_r5n0gr")
def test_long():
    """Finds the order from many words in time"""
    rng = random.Random(203)
    alphabet = list(string.ascii_lowercase)
    rng.shuffle(alphabet)
    place = {letter: index for index, letter in enumerate(alphabet)}
    words = sorted(
        {"".join(rng.choices(alphabet, k=rng.randint(1, 8))) for _ in range(WORDS)},
        key=lambda word: [place[letter] for letter in word],
    )
    while len(words) < WORDS:
        words.append(words[-1])
    order = letter_order(words)
    assert sorts(order, words)
    assert letter_order(words + [words[0]]) == ""
