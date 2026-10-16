import random
import string

import pytest
from anagrams import anagram_groups

WORDS = 50_000


def by_comparing(words):
    """The groups, found by comparing each word with the first word of each group so far."""
    groups = []
    for word in words:
        for group in groups:
            if sorted(group[0]) == sorted(word):
                group.append(word)
                break
        else:
            groups.append([word])
    return groups


@pytest.mark.id("tst_ej8cop")
def test_groups():
    """Groups each word with its anagrams"""
    words = ["listen", "stone", "silent", "notes", "enlist", "tones", "rat"]
    assert anagram_groups(words) == [
        ["listen", "silent", "enlist"],
        ["stone", "notes", "tones"],
        ["rat"],
    ]


@pytest.mark.id("tst_vsmfat")
def test_alone():
    """Keeps a word with no anagram alone, a repeated word twice, and no words as none"""
    assert anagram_groups(["ab", "cd"]) == [["ab"], ["cd"]]
    assert anagram_groups(["tea", "eat", "tea"]) == [["tea", "eat", "tea"]]
    assert anagram_groups([]) == []


@pytest.mark.id("tst_cjsryi")
def test_comparing():
    """Matches comparing words with each group"""
    rng = random.Random(13)
    for _ in range(200):
        count = rng.randint(0, 10)
        words = ["".join(rng.choices("abc", k=rng.randint(1, 3))) for _ in range(count)]
        assert anagram_groups(words) == by_comparing(words)


@pytest.mark.id("tst_094n64")
def test_long():
    """Groups a long list of words in time"""
    rng = random.Random(14)
    roots = [
        "".join(rng.choices(string.ascii_lowercase, k=8)) for _ in range(WORDS // 2)
    ]
    words = roots + ["".join(rng.sample(root, 8)) for root in roots]
    groups = anagram_groups(words)
    assert sum(len(group) for group in groups) == WORDS
    keys = ["".join(sorted(root)) for root in roots]
    assert len(groups) == len(dict.fromkeys(keys))
