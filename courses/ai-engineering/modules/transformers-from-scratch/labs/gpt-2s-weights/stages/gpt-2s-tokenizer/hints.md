`[*range(ord("!"), ord("~") + 1), *range(ord("¡"), ord("¬") + 1), *range(ord("®"), ord("ÿ") + 1)]` lists the bytes that keep their character. Walk the bytes from 0 to 255, giving each of the others `chr(256 + n)`, with `n` counting up from 0.

---

Make the merges' ranks once: `{pair: rank for rank, pair in enumerate(merges)}`. Then `min(pairs, key=lambda pair: ranks.get(pair, len(ranks)))` finds the pair to join next, and when that pair isn't in `ranks`, no merge is left.

---

In `decode`, join the tokens' strings and turn their characters back into bytes, then decode all the bytes at once: one character can take more than one token.
