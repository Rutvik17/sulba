`regex.findall(PATTERN, text)` splits a text into its pieces, and `piece.encode()` gives a piece's bytes. A `Counter` of the pieces holds each distinct piece once with its count, so a pair's count is the sum of the counts of the pieces it occurs in, once for each time it occurs in each.

---

`max(pairs, key=pairs.__getitem__)` gives the commonest pair and, of tied pairs, the one counted first. Count the pieces in the order they first occur, and each piece's pairs from left to right, and the one counted first is the one that occurs first in the texts.

---

To join a pair in a piece, walk its tokens with an index: where the pair starts, add the joined token and step two; elsewhere, add the token and step one.
