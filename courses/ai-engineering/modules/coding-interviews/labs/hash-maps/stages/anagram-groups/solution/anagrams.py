def anagram_groups(words):
    """The words grouped with their anagrams, in the order they appear."""
    groups = {}
    for word in words:
        groups.setdefault("".join(sorted(word)), []).append(word)
    return list(groups.values())
