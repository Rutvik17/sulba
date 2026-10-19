from collections import Counter

import pytest

from tokenizer import END, PATTERN, decode, encode, stories, train

FILE = "data/TinyStoriesV2-GPT4-valid.txt"


@pytest.fixture(scope="module")
def told():
    return stories(FILE)


def recount(texts, size):
    """The merges train should give, with every pair counted again for each merge."""
    counts = Counter(piece for text in texts for piece in PATTERN.findall(text))
    words = {tuple(piece.encode()): weight for piece, weight in counts.items()}
    merges = []
    while 256 + len(merges) < size - 1:
        pairs = Counter()
        for word, weight in words.items():
            for pair in zip(word, word[1:]):
                pairs[pair] += weight
        if not pairs:
            break
        best = min(pairs, key=lambda pair: (-pairs[pair], pair))
        new = 256 + len(merges)
        merges.append(best)
        merged_words = Counter()
        for word, weight in words.items():
            merged, at = [], 0
            while at < len(word):
                if word[at : at + 2] == best:
                    merged.append(new)
                    at += 2
                else:
                    merged.append(word[at])
                    at += 1
            merged_words[tuple(merged)] += weight
        words = merged_words
    return merges


@pytest.mark.id("tst_6kdcm3")
def test_stories(told):
    """Every whole story in the file, trimmed"""
    assert len(told) == 27629
    assert told[0].startswith(
        "Once upon a time, in a warm and sunny place, there was a big pit."
    )
    assert told[-1].endswith(
        "Cally and her friends saved the oasis and were very happy."
    )
    assert all(story and story == story.strip() for story in told)
    assert not any(END in story for story in told)


@pytest.mark.id("tst_mim5da")
def test_merges(told):
    """The merges counting every pair again gives"""
    sample = told[:200]
    assert train(sample, 500) == recount(sample, 500)
    assert train(told[200:300], 300) == recount(told[200:300], 300)


@pytest.mark.id("tst_a4jg7e")
def test_ties():
    """Of pairs seen as often, the one whose numbers come first"""
    # " c", "cd" and "ab" are each seen twice, and " c" is (32, 99).
    assert train(["ab cd ab cd"], 258) == [(32, 99)]
    assert train(["ba", "ab"], 258) == [(97, 98)]


@pytest.mark.id("tst_u87fpi")
def test_vocabulary_size(told):
    """size tokens with the separator, or fewer once no pair is left"""
    assert len(train(told[:50], 300)) == 300 - 257
    assert train(["aaaa"], 1000) == [(97, 97), (256, 256)]


@pytest.mark.id("tst_vk03sy")
def test_round_trip(told):
    """Stories and their separators, back as they were"""
    merges = train(told[:300], 700)
    text = END.join(told[300:400]) + END
    tokens = encode(text, merges)
    assert decode(tokens, merges) == text
    assert tokens.count(699) == 100
    assert max(tokens) == 699
    assert encode("Tim ran." + END, merges)[-1] == 699
    assert decode(encode("Lily saw a 🐶!", merges), merges) == "Lily saw a 🐶!"


@pytest.mark.id("tst_wjdzwe")
def test_the_whole_file(told):
    """All the stories, learnt from and encoded"""
    merges = train(told, 2048)
    tokens = encode(END.join(told) + END, merges)
    assert len(merges) == 2048 - 257
    assert len(tokens) == 6026933
