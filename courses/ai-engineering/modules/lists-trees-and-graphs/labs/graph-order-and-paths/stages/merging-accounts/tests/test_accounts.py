import random

import pytest
from accounts import merged

ACCOUNTS = 50_000


def plain(accounts):
    """The merged accounts, by merging any two that share an address until none do."""
    people = [[name, set(addresses)] for name, *addresses in accounts]
    joined = True
    while joined:
        joined = False
        for first in range(len(people)):
            for second in range(first + 1, len(people)):
                if people[first][1] & people[second][1]:
                    people[first][1] |= people.pop(second)[1]
                    joined = True
                    break
            if joined:
                break
    return [[name, *sorted(addresses)] for name, addresses in people]


def same(found, expected):
    """Whether the two lists hold the same accounts, in any order."""
    return sorted(found) == sorted(expected)


@pytest.mark.id("tst_7q4mb8")
def test_merged():
    """Merges the accounts that share addresses"""
    accounts = [
        ["Ada", "ada@work.com", "ada@home.com"],
        ["Ada", "ada@old.com"],
        ["Ada", "ada@home.com", "ada@phone.com"],
        ["Bo", "bo@home.com"],
    ]
    assert same(
        merged(accounts),
        [
            ["Ada", "ada@home.com", "ada@phone.com", "ada@work.com"],
            ["Ada", "ada@old.com"],
            ["Bo", "bo@home.com"],
        ],
    )


@pytest.mark.id("tst_u0k15s")
def test_edges():
    """Keeps a lone account, lists an address once, and merges through a chain of accounts"""
    assert merged([]) == []
    assert same(merged([["Cy", "c@x.com"]]), [["Cy", "c@x.com"]])
    assert same(merged([["Cy", "c@x.com", "c@x.com"]]), [["Cy", "c@x.com"]])
    chain = [
        ["Di", "a@x.com", "b@x.com"],
        ["Di", "c@x.com", "d@x.com"],
        ["Di", "b@x.com", "c@x.com"],
    ]
    assert same(merged(chain), [["Di", "a@x.com", "b@x.com", "c@x.com", "d@x.com"]])


@pytest.mark.id("tst_htlbl3")
def test_random():
    """Matches merging until no two accounts share an address, on random lists"""
    rng = random.Random(205)
    for _ in range(300):
        people = rng.randint(1, 5)
        accounts = []
        for _ in range(rng.randint(1, 8)):
            person = rng.randrange(people)
            name = "AB"[person % 2]
            addresses = [
                f"{person}.{rng.randrange(4)}@x.com" for _ in range(rng.randint(1, 3))
            ]
            accounts.append([name, *addresses])
        assert same(merged(accounts), plain(accounts))


@pytest.mark.id("tst_ehm06n")
def test_long():
    """Merges a long chain of accounts in time"""
    chain = [
        ["Ev", f"{place}@x.com", f"{place + 1}@x.com"] for place in range(ACCOUNTS)
    ]
    random.Random(206).shuffle(chain)
    (person,) = merged(chain)
    assert person == ["Ev", *sorted(f"{place}@x.com" for place in range(ACCOUNTS + 1))]
