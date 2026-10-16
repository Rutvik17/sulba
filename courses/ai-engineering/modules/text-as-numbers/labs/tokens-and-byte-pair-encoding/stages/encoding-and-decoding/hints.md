For a piece's list of tokens as bytes, `ranks.get(a + b)` gives the rank of the token a neighbouring pair `a, b` would join into, or None. Of the pairs that join, merge the one of lowest rank; when the same pair occurs twice, the first.

---

`tokens[i : i + 2] = [tokens[i] + tokens[i + 1]]` merges the pair at `i` in place.

---

A dict from rank to bytes, `{rank: token for token, rank in ranks.items()}`, turns each token back into its bytes. `b"".join(...)` joins them, and `.decode(errors="replace")` reads them.
