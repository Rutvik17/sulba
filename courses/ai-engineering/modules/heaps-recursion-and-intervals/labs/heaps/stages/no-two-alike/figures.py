import math
from collections import Counter

# The longest test, as tests/test_reorganize.py sets it: the letters a to j, each as often.
LETTERS = 200_000


def figures():
    counts = Counter({letter: LETTERS // 10 for letter in "abcdefghij"})
    # The orders of a multiset: n! over the product of each letter's count factorial.
    log10 = math.lgamma(LETTERS + 1) - sum(math.lgamma(c + 1) for c in counts.values())
    return {"letters": f"{LETTERS:,}", "digits": f"{int(log10 / math.log(10)) + 1:,}"}
